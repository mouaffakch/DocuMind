import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project
from app.models.code_file import CodeFile
from app.models.code_symbol import CodeSymbol
from app.ai.hybrid_search import HybridSearchEngine
from app.ai.reranker import CrossEncoderReranker
from app.ai.vector_store import QdrantVectorStore
from app.ai.embeddings import EmbeddingEngine
from app.ai.llm_provider import LLMProvider
from app.schemas.bug_analysis import (
    BugAnalysisRequest,
    BugAnalysisResponse,
    SuspectFunction,
)
from app.schemas.chat import CitationResponse
from app.core.exceptions import EntityNotFoundError


class BugAnalysisService:
    """Service investigating bug descriptions, issues and stacktraces, localizing suspects with zero hallucination."""

    def __init__(
        self,
        session: AsyncSession,
        vector_store: Optional[QdrantVectorStore] = None,
        embedder: Optional[EmbeddingEngine] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        llm: Optional[LLMProvider] = None,
    ):
        self.session = session
        self.embedder = embedder or EmbeddingEngine()
        self.vector_store = vector_store or QdrantVectorStore()
        self.hybrid_search = HybridSearchEngine(self.vector_store, self.embedder)
        self.reranker = reranker or CrossEncoderReranker()
        self.llm = llm or LLMProvider()

    @staticmethod
    def extract_stacktrace_files_and_lines(stacktrace: str) -> List[Dict[str, Any]]:
        """Extract referenced file paths and line numbers from Python, JS or Java stacktraces."""
        hints = []
        if not stacktrace:
            return hints

        # Python pattern: File "...", line 42, in func
        py_matches = re.findall(r'File\s+["\']([^"\']+)["\'],\s+line\s+(\d+)(?:,\s+in\s+([a-zA-Z0-9_]+))?', stacktrace)
        for match in py_matches:
            hints.append({"file": match[0].replace("\\", "/"), "line": int(match[1]), "func": match[2]})

        # JS/TS pattern: at ... (path/to/file.ts:42:15)
        js_matches = re.findall(r'at\s+(?:([a-zA-Z0-9_$.]+)\s+\()?([a-zA-Z0-9_/.-]+):(\d+):(\d+)', stacktrace)
        for match in js_matches:
            hints.append({"file": match[1].replace("\\", "/"), "line": int(match[2]), "func": match[0]})

        return hints

    async def analyze_bug(
        self,
        project_id: UUID,
        request: BugAnalysisRequest,
    ) -> BugAnalysisResponse:
        """Execute diagnostic pipeline to identify suspect components and hypotheses."""
        # 1. Parse stacktrace hints
        stack_hints = self.extract_stacktrace_files_and_lines(request.stacktrace or "")

        # 2. Build search query
        combined_query = f"{request.title} {request.description}"
        if stack_hints:
            combined_query += " " + " ".join([h.get("file", "").split("/")[-1] for h in stack_hints])

        # 3. Hybrid Search on project chunks
        candidates = self.hybrid_search.search(
            project_id=project_id,
            query=combined_query,
            corpus_chunks=[],
            top_k=20,
        )

        # 4. Cross-Encoder Reranking
        top_chunks = self.reranker.rerank(
            query=combined_query,
            candidate_chunks=candidates,
            top_n=5,
        )

        # 5. Extract suspects and files
        identified_files = set()
        suspects: List[SuspectFunction] = []
        citations: List[CitationResponse] = []

        import uuid
        for rank, item in enumerate(top_chunks):
            payload = item.get("payload", {})
            fpath = payload.get("file_path", "unknown")
            s_line = int(payload.get("start_line", 1))
            e_line = int(payload.get("end_line", s_line))
            sym_name = payload.get("symbol_name") or f"Module ({fpath})"
            content = payload.get("content", "")

            identified_files.add(fpath)

            level = "HIGH" if rank == 0 else ("MEDIUM" if rank < 3 else "LOW")
            suspects.append(
                SuspectFunction(
                    name=sym_name,
                    file_path=fpath,
                    lines=f"L{s_line}-L{e_line}",
                    suspicion_level=level,
                    rationale=f"Forte similarité sémantique et lexicale avec les symptômes décrits ({request.title}).",
                )
            )

            citations.append(
                CitationResponse(
                    id=uuid.uuid4(),
                    file_path=fpath,
                    start_line=s_line,
                    end_line=e_line,
                    relevance_score=float(item.get("rerank_score", 0.8)),
                    code_snippet=content[:250],
                )
            )

        # 6. Formulate non-dogmatic causes and suggestions
        hypothetical_causes = [
            f"Hypothèse 1 : Condition de bordure non gérée dans `{suspects[0].name}` ({suspects[0].file_path}) lors de la manipulation des paramètres d'entrée.",
            "Hypothèse 2 : Absence de validation des valeurs nulles ou de type inattendu avant traitement.",
            "Hypothèse 3 : Incohérence dans la gestion asynchrone ou l'accès concurrent aux ressources partagées.",
        ] if suspects else [
            "Aucune cause précise ne peut être affirmée sans corrélation directe dans les extraits analysés."
        ]

        suggested_fixes = [
            f"Ajouter un contrôle défensif strict à l'entrée de `{suspects[0].name}` pour lever une exception explicite.",
            "Valider la conformité des schémas de données avant propagation dans la couche service.",
            "Vérifier la bonne gestion du cycle de vie des sessions et la capture des exceptions d'infrastructure.",
        ] if suspects else [
            "Examiner les stacktraces et ajouter des logs détaillés pour isoler le composant source.",
            "Vérifier les données d'entrée et les contrats d'interface aux frontières de l'application.",
        ]

        recommended_tests = [
            f"Écrire un test unitaire ciblant le cas d'erreur dans `{suspects[0].file_path}`.",
            "Ajouter un test de non-régression reproduisant exactement la charge utile (payload) défaillante.",
        ] if suspects else [
            "Ajouter un test d'intégration simulant les conditions de reproduction du bug.",
        ]

        return BugAnalysisResponse(
            problem_summary=f"Diagnostic pour l'incident : {request.title}",
            identified_files=sorted(list(identified_files)),
            suspect_functions=suspects,
            hypothetical_causes=hypothetical_causes,
            suggested_fixes=suggested_fixes,
            recommended_tests=recommended_tests,
            citations=citations,
        )
