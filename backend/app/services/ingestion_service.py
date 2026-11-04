import os
import shutil
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.code_file import CodeFile
from app.models.code_symbol import CodeSymbol
from app.models.dependency import SymbolDependency
from app.repositories.project_repository import ProjectRepository
from app.ingestion.git_cloner import GitCloner
from app.ingestion.file_scanner import FileScanner, ScannedFile
from app.ingestion.ast_parser import ASTParser
from app.ingestion.call_graph_extractor import CallGraphExtractor
from app.ingestion.chunker import ASTAwareChunker, CodeChunk
from app.ai.embeddings import EmbeddingEngine
from app.ai.vector_store import QdrantVectorStore
from app.core.exceptions import EntityNotFoundError, IngestionError


class IngestionService:
    """Orchestrates source code cloning, filtering, AST parsing, chunking, and vector indexing."""

    def __init__(
        self,
        session: AsyncSession,
        vector_store: Optional[QdrantVectorStore] = None,
        embedder: Optional[EmbeddingEngine] = None,
        auth_service=None,
    ):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedder = embedder or EmbeddingEngine()
        self.auth_service = auth_service

    async def ingest_project(
        self,
        project_id: UUID,
        user: User,
        local_source_dir: Optional[str] = None,
    ) -> Project:
        """Run full ingestion pipeline for a project."""
        project = await self.project_repo.get_by_owner_and_id(user.id, project_id)
        if not project:
            raise EntityNotFoundError(f"Projet introuvable ({project_id}).")

        project.status = ProjectStatus.INDEXING
        project.error_message = None
        await self.project_repo.update(project)

        temp_clone_dir = f"./cloned_repos/{project.id}"
        source_dir = local_source_dir or temp_clone_dir
        should_cleanup = local_source_dir is None

        try:
            # 1. Clone if remote
            if not local_source_dir:
                pat = self.auth_service.get_decrypted_pat(user) if self.auth_service else None
                GitCloner.clone_repository(
                    repo_url=project.repo_url,
                    target_dir=temp_clone_dir,
                    branch=project.default_branch,
                    pat=pat,
                )

            # 2. Scan Files
            scanned_files = FileScanner.scan_directory(source_dir)
            if not scanned_files:
                raise IngestionError("Aucun fichier de code ou de documentation exploitable trouvé dans le dépôt.")

            # Clear previous files, symbols & dependencies for this project if re-indexing
            await self.session.execute(delete(CodeFile).where(CodeFile.project_id == project.id))
            await self.session.execute(delete(SymbolDependency).where(SymbolDependency.project_id == project.id))
            self.vector_store.delete_project_vectors(project.id)

            total_symbols_count = 0
            all_chunks: List[CodeChunk] = []

            for sfile in scanned_files:
                # Create CodeFile entity
                code_file = CodeFile(
                    project_id=project.id,
                    file_path=sfile.relative_path,
                    language=sfile.language,
                    size_bytes=sfile.size_bytes,
                    sha256_hash=sfile.sha256_hash,
                )
                self.session.add(code_file)
                await self.session.flush()

                # Parse AST
                parsed_symbols = ASTParser.parse_code(sfile.content, sfile.language)
                for psym in parsed_symbols:
                    sym_entity = CodeSymbol(
                        file_id=code_file.id,
                        name=psym.name,
                        symbol_type=psym.symbol_type,
                        start_line=psym.start_line,
                        end_line=psym.end_line,
                        signature=psym.signature,
                        docstring=psym.docstring,
                    )
                    self.session.add(sym_entity)
                    total_symbols_count += 1

                # Chunk file
                file_chunks = ASTAwareChunker.chunk_file(sfile, parsed_symbols)
                all_chunks.extend(file_chunks)

                # Extract Call Dependencies
                file_deps = CallGraphExtractor.extract_dependencies(sfile.content, sfile.language, sfile.relative_path)
                for dep in file_deps:
                    dep_entity = SymbolDependency(
                        project_id=project.id,
                        caller_name=dep.caller_name,
                        caller_file_path=dep.caller_file_path,
                        caller_line=dep.caller_line,
                        callee_name=dep.callee_name,
                        dependency_type=dep.dependency_type,
                    )
                    self.session.add(dep_entity)

            # 3. Vectorize & Index in Qdrant
            chunk_contents = [c.content for c in all_chunks]
            chunk_vectors = self.embedder.embed_documents(chunk_contents)

            self.vector_store.upsert_chunks(
                project_id=project.id,
                chunks=all_chunks,
                vectors=chunk_vectors,
                commit_sha=project.latest_commit_sha,
            )

            # 4. Finalize project stats
            project.status = ProjectStatus.READY
            project.total_files = len(scanned_files)
            project.total_chunks = len(all_chunks)
            project.total_symbols = total_symbols_count
            project.last_synced_at = datetime.now(timezone.utc)
            await self.project_repo.update(project)

            return project

        except Exception as exc:
            project.status = ProjectStatus.ERROR
            project.error_message = str(exc)
            await self.project_repo.update(project)
            raise IngestionError(f"Erreur durant l'ingestion du dépôt: {str(exc)}") from exc

        finally:
            if should_cleanup and os.path.exists(temp_clone_dir):
                GitCloner.cleanup_directory(temp_clone_dir)

    async def list_project_files(self, project_id: UUID, user: User) -> List[CodeFile]:
        """List all indexed code files for a project."""
        project = await self.project_repo.get_by_owner_and_id(user.id, project_id)
        if not project:
            raise EntityNotFoundError(f"Projet introuvable ({project_id}).")

        stmt = select(CodeFile).where(CodeFile.project_id == project_id).order_by(CodeFile.file_path.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_file_symbols(self, file_id: UUID, user: User) -> List[CodeSymbol]:
        """List AST symbols for a specific file."""
        stmt = select(CodeSymbol).where(CodeSymbol.file_id == file_id).order_by(CodeSymbol.start_line.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
