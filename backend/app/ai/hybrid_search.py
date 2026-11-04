import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from rank_bm25 import BM25Okapi
from app.ai.vector_store import QdrantVectorStore
from app.ai.embeddings import EmbeddingEngine


class CodeTokenizer:
    """Tokenizer tailored for programming languages: handles camelCase, snake_case, and symbols."""

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        # Split on snake_case, camelCase boundaries, and non-alphanumeric chars
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+|[a-zA-Z]+", text)
        tokens = [w.lower() for w in words if len(w) > 1]
        return tokens


class HybridSearchEngine:
    """Fuses Dense Vector Search and Sparse BM25 Lexical Search via Reciprocal Rank Fusion (RRF)."""

    def __init__(self, vector_store: QdrantVectorStore, embedder: EmbeddingEngine):
        self.vector_store = vector_store
        self.embedder = embedder

    def search(
        self,
        project_id: UUID,
        query: str,
        corpus_chunks: List[Dict[str, Any]],
        top_k: int = 25,
        dense_limit: int = 20,
        bm25_limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search and return Reciprocal Rank Fused results.
        `corpus_chunks` provides the in-memory or cached chunk payloads for BM25 indexing.
        """
        # 1. Dense Semantic Search
        query_vector = self.embedder.embed_text(query)
        dense_hits = self.vector_store.search_similar(
            project_id=project_id,
            query_vector=query_vector,
            limit=dense_limit,
        )

        # 2. Sparse BM25 Lexical Search
        bm25_hits: List[Dict[str, Any]] = []
        if corpus_chunks:
            tokenized_corpus = [
                CodeTokenizer.tokenize(c.get("content", "")) for c in corpus_chunks
            ]
            tokenized_query = CodeTokenizer.tokenize(query)

            if tokenized_query and any(len(doc) > 0 for doc in tokenized_corpus):
                bm25 = BM25Okapi(tokenized_corpus)
                scores = bm25.get_scores(tokenized_query)
                # Sort indices by score desc
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:bm25_limit]
                for idx in top_indices:
                    if scores[idx] > 0.1:  # Filter trivial matches
                        chunk = corpus_chunks[idx]
                        bm25_hits.append(
                            {
                                "id": chunk.get("chunk_id", str(idx)),
                                "score": float(scores[idx]),
                                "payload": chunk,
                            }
                        )

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF formula: RRF_score = sum( 1 / (60 + rank_i) )
        k_const = 60
        rrf_scores: Dict[str, float] = {}
        candidate_map: Dict[str, Dict[str, Any]] = {}

        # Add Dense ranks
        for rank, hit in enumerate(dense_hits, start=1):
            chunk_id = str(hit.get("id"))
            candidate_map[chunk_id] = hit
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k_const + rank))

        # Add BM25 ranks
        for rank, hit in enumerate(bm25_hits, start=1):
            chunk_id = str(hit.get("id"))
            if chunk_id not in candidate_map:
                candidate_map[chunk_id] = hit
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k_const + rank))

        # Sort combined results by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        fused_results: List[Dict[str, Any]] = []
        for cid in sorted_ids:
            item = candidate_map[cid]
            item["rrf_score"] = rrf_scores[cid]
            fused_results.append(item)

        return fused_results
