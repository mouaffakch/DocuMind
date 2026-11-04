import time
import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.ai.embeddings import EmbeddingEngine
from app.ai.vector_store import QdrantVectorStore
from app.ai.hybrid_search import HybridSearchEngine
from app.ai.reranker import CrossEncoderReranker
from app.ai.llm_provider import LLMProvider


class CitationData:
    """Represents a verified citation linked to a generated response."""
    def __init__(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        relevance_score: float,
        code_snippet: Optional[str] = None,
    ):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.relevance_score = relevance_score
        self.code_snippet = code_snippet


class RAGResponse:
    """Output bundle of the RAG pipeline."""
    def __init__(self, content: str, citations: List[CitationData], execution_time_seconds: float):
        self.content = content
        self.citations = citations
        self.execution_time_seconds = execution_time_seconds


class RAGPipeline:
    """Orchestrates hybrid retrieval, cross-encoder reranking, context assembly, and grounded generation."""

    SYSTEM_PROMPT = """Tu es DocuMind, un assistant expert en génie logiciel et analyse de code source.
Tu réponds aux questions des développeurs avec clarté, rigueur et professionnalisme.

RÈGLES IMPÉRATIVES DE GROUNDING ET ANTI-HALLUCINATION :
1. Tu dois répondre EXCLUSIVEMENT en t'appuyant sur les extraits de code fournis dans le CONTEXTE ci-dessous.
2. Pour chaque affirmation technique, cite le fichier exact et les numéros de lignes sous la forme `[nom_fichier:Lxx-Lyy]`.
3. Si le contexte fourni ne contient pas les éléments suffisants pour répondre avec certitude, réponds mot pour mot :
   "Les éléments indexés du dépôt ne permettent pas de répondre précisément à cette question."
4. Ne fais AUCUNE supposition non étayée par le code fourni.
"""

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedder: Optional[EmbeddingEngine] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.embedder = embedder or EmbeddingEngine()
        self.vector_store = vector_store or QdrantVectorStore()
        self.hybrid_search = HybridSearchEngine(self.vector_store, self.embedder)
        self.reranker = reranker or CrossEncoderReranker()
        self.llm = llm_provider or LLMProvider()

    async def execute(
        self,
        project_id: UUID,
        query: str,
        corpus_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """Execute the end-to-end RAG pipeline for a user question."""
        start_time = time.time()

        # 1. Hybrid Retrieval (Dense + BM25 with Reciprocal Rank Fusion)
        fused_candidates = self.hybrid_search.search(
            project_id=project_id,
            query=query,
            corpus_chunks=corpus_chunks,
            top_k=25,
        )

        # 2. Cross-Encoder Reranking
        top_chunks = self.reranker.rerank(
            query=query,
            candidate_chunks=fused_candidates,
            top_n=5,
        )

        # 3. Context Construction
        context_parts = []
        citations_data: List[CitationData] = []

        for i, item in enumerate(top_chunks, start=1):
            payload = item.get("payload", {})
            fpath = payload.get("file_path", "unknown")
            s_line = int(payload.get("start_line", 1))
            e_line = int(payload.get("end_line", s_line))
            score = float(item.get("rerank_score", item.get("rrf_score", 0.0)))
            content = payload.get("content", "")

            header = f"--- [EXTRAIT {i} - {fpath} - Lignes {s_line}-{e_line}] ---"
            context_parts.append(f"{header}\n{content}")

            citations_data.append(
                CitationData(
                    file_path=fpath,
                    start_line=s_line,
                    end_line=e_line,
                    relevance_score=score,
                    code_snippet=content[:300],
                )
            )

        context_block = "\n\n".join(context_parts) if context_parts else "AUCUN EXTRAIT DISPONIBLE."

        # Assemble user prompt with conversation history context
        history_text = ""
        if conversation_history:
            history_text = "Historique récent de la discussion :\n"
            for msg in conversation_history[-4:]:  # Keep last 4 turns
                history_text += f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}\n"
            history_text += "\n"

        user_prompt = (
            f"{history_text}"
            f"CONTEXTE EXTRAIT DU DÉPÔT :\n{context_block}\n\n"
            f"QUESTION DU DÉVELOPPEUR :\n{query}\n\n"
            f"RÉPONSE STRUCTURÉE (avec citations de lignes) :"
        )

        # 4. LLM Generation
        answer_text = await self.llm.generate_completion(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        execution_time = time.time() - start_time

        return RAGResponse(
            content=answer_text,
            citations=citations_data,
            execution_time_seconds=round(execution_time, 3),
        )
