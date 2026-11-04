from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.project import Project
from app.models.code_file import CodeFile
from app.models.code_symbol import CodeSymbol, SymbolType
from app.models.dependency import SymbolDependency, DependencyType
from app.models.documentation import DocumentationExport, DocumentationType
from app.schemas.documentation import (
    DocumentationGenerateRequest,
    DocumentationExportResponse,
)
from app.repositories.project_repository import ProjectRepository
from app.core.exceptions import EntityNotFoundError


class DocService:
    """Service generating technical documentation, summaries and Mermaid UML diagrams."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)

    async def generate_documentation(
        self,
        user: User,
        project_id: UUID,
        request: DocumentationGenerateRequest,
    ) -> DocumentationExportResponse:
        """Generate structured Markdown documentation and/or UML diagrams."""
        project = await self.project_repo.get_by_owner_and_id(user.id, project_id)
        if not project:
            raise EntityNotFoundError(f"Projet introuvable ({project_id}).")

        # 1. Fetch project symbols & dependencies
        sym_stmt = (
            select(CodeSymbol, CodeFile.file_path)
            .join(CodeFile, CodeSymbol.file_id == CodeFile.id)
            .where(CodeFile.project_id == project_id)
        )
        sym_res = await self.session.execute(sym_stmt)
        all_symbols = sym_res.all()

        dep_stmt = select(SymbolDependency).where(SymbolDependency.project_id == project_id)
        dep_res = await self.session.execute(dep_stmt)
        all_deps = list(dep_res.scalars().all())

        title = f"Documentation Technique — {project.name}"
        markdown_content = ""
        mermaid_diagram = None

        if request.doc_type == DocumentationType.UML_DIAGRAM:
            title = f"Diagramme de Classes UML — {project.name}"
            mermaid_diagram = self._build_mermaid_class_diagram(all_symbols, all_deps)
            markdown_content = (
                f"# {title}\n\n"
                f"Ce diagramme modélise l'architecture des classes et leurs relations déduites de l'analyse syntaxique statique (Tree-sitter).\n\n"
                f"```mermaid\n{mermaid_diagram}\n```\n"
            )

        elif request.doc_type == DocumentationType.MODULE and request.target_module:
            title = f"Documentation du Module `{request.target_module}`"
            markdown_content = self._build_module_doc(request.target_module, all_symbols)

        else:
            # PROJECT_OVERVIEW
            title = f"Architecture Globale & Vue d'Ensemble — {project.name}"
            uml_part = self._build_mermaid_class_diagram(all_symbols, all_deps) if request.include_uml else ""
            mermaid_diagram = uml_part if request.include_uml else None
            markdown_content = self._build_project_overview(project, all_symbols, uml_part)

        # 2. Persist export
        export_record = DocumentationExport(
            project_id=project.id,
            user_id=user.id,
            title=title,
            doc_type=request.doc_type,
            target_module=request.target_module,
            content_markdown=markdown_content,
            mermaid_diagram=mermaid_diagram,
        )
        self.session.add(export_record)
        await self.session.flush()
        await self.session.refresh(export_record)

        return DocumentationExportResponse.model_validate(export_record)

    async def list_exports(self, user: User, project_id: UUID) -> List[DocumentationExportResponse]:
        """List past generated documentation exports for a project."""
        stmt = (
            select(DocumentationExport)
            .where(DocumentationExport.project_id == project_id, DocumentationExport.user_id == user.id)
            .order_by(DocumentationExport.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [DocumentationExportResponse.model_validate(e) for e in res.scalars().all()]

    async def get_export(self, user: User, export_id: UUID) -> DocumentationExportResponse:
        """Get an existing documentation export."""
        stmt = select(DocumentationExport).where(DocumentationExport.id == export_id, DocumentationExport.user_id == user.id)
        res = await self.session.execute(stmt)
        record = res.scalars().first()
        if not record:
            raise EntityNotFoundError("Document introuvable.")
        return DocumentationExportResponse.model_validate(record)

    async def delete_export(self, user: User, export_id: UUID) -> None:
        """Delete an export record."""
        stmt = select(DocumentationExport).where(DocumentationExport.id == export_id, DocumentationExport.user_id == user.id)
        res = await self.session.execute(stmt)
        record = res.scalars().first()
        if not record:
            raise EntityNotFoundError("Document introuvable.")
        await self.session.delete(record)

    @staticmethod
    def _build_mermaid_class_diagram(symbols: list, deps: List[SymbolDependency]) -> str:
        """Generate valid Mermaid classDiagram syntax from extracted AST symbols and calls."""
        diagram = "classDiagram\n"
        classes = {}
        for sym, fpath in symbols:
            if sym.symbol_type in (SymbolType.CLASS, SymbolType.INTERFACE):
                cname = sym.name.replace(".", "_").replace(" ", "_")
                classes[cname] = {"type": sym.symbol_type.value, "methods": []}

        for sym, fpath in symbols:
            if sym.symbol_type == SymbolType.METHOD and "." in sym.name:
                parent_c, mname = sym.name.split(".", 1)
                parent_clean = parent_c.replace(".", "_")
                if parent_clean in classes:
                    classes[parent_clean]["methods"].append(mname)

        if not classes:
            # Fallback if no classes detected
            return "classDiagram\n    class DocuMindComponent {\n        +execute()\n    }"

        for cname, data in list(classes.items())[:12]:  # Limit to 12 classes for readability
            diagram += f"    class {cname} {{\n"
            for m in data["methods"][:6]:
                clean_m = m.replace("(", "").replace(")", "").replace(" ", "_")
                diagram += f"        +{clean_m}()\n"
            diagram += "    }\n"

        # Add relationships
        linked = set()
        for d in deps:
            c1 = d.caller_name.split(".")[0].replace(" ", "_")
            c2 = d.callee_name.split(".")[0].replace(" ", "_")
            if c1 in classes and c2 in classes and c1 != c2:
                pair = f"{c1} --> {c2}"
                if pair not in linked:
                    linked.add(pair)
                    diagram += f"    {c1} --> {c2} : calls\n"

        return diagram

    @staticmethod
    def _build_module_doc(module_path: str, symbols: list) -> str:
        """Generate markdown doc for a specific module."""
        doc = f"# Spécification du Module `{module_path}`\n\n"
        doc += "## Symboles et Composants Identifiés\n\n"
        module_syms = [s for s, fpath in symbols if module_path.lower() in fpath.lower()]
        if not module_syms:
            doc += "Aucun symbole AST spécifique n'a été détecté dans ce module.\n"
            return doc

        for s in module_syms:
            doc += f"### `{s.name}` ({s.symbol_type.value})\n"
            doc += f"- **Emplacement :** Lignes {s.start_line} à {s.end_line}\n"
            if s.signature:
                doc += f"- **Signature :** `{s.signature}`\n"
            if s.docstring:
                doc += f"- **Description :** {s.docstring}\n"
            doc += "\n"

        return doc

    @staticmethod
    def _build_project_overview(project: Project, symbols: list, uml_diagram: str) -> str:
        """Generate comprehensive architectural overview."""
        doc = f"# Documentation d'Architecture : {project.name}\n\n"
        doc += f"**Dépôt GitHub :** `{project.repo_full_name}`  \n"
        doc += f"**Branche analysée :** `{project.default_branch}`  \n"
        doc += f"**Fichiers indexés :** {project.total_files} | **Unités AST :** {project.total_symbols} | **Chunks :** {project.total_chunks}\n\n"

        doc += "## 1. Description du Projet\n"
        doc += f"{project.description or 'Aucune description fournie par le dépôt.'}\n\n"

        doc += "## 2. Cartographie des Composants Clés\n\n"
        classes = [s for s, _ in symbols if s.symbol_type == SymbolType.CLASS]
        functions = [s for s, _ in symbols if s.symbol_type == SymbolType.FUNCTION]
        doc += f"- **Nombre de Classes principales :** {len(classes)}\n"
        doc += f"- **Nombre de Fonctions exportées :** {len(functions)}\n\n"

        if uml_diagram:
            doc += "## 3. Diagramme de Classes UML\n\n"
            doc += f"```mermaid\n{uml_diagram}\n```\n\n"

        doc += "## 4. Recommandations de Maintenance\n"
        doc += "- Veiller à maintenir la documentation à jour lors de l'ajout de nouvelles interfaces.\n"
        doc += "- Consulter le module *Impact Analysis* de DocuMind avant toute refactorisation sensible.\n"

        return doc
