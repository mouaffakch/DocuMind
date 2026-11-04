from typing import List, Dict, Any, Tuple
import re
from app.core.config import settings


class CrossEncoderReranker:
    """Reranks retrieved candidate chunks using cross-attention scoring to maximize precision."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", use_mock: bool = False):
        import os
        self.model_name = model_name
        self.use_mock = use_mock or os.getenv("DOCUMIND_TESTING") == "true" or settings.ENVIRONMENT == "testing"
        self._model = None

    def _load_model(self):
        if self._model is None and not self.use_mock:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception:
                self.use_mock = True

    def rerank(
        self,
        query: str,
        candidate_chunks: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Rerank candidates and return the Top N most relevant chunks."""
        if not candidate_chunks:
            return []

        if len(candidate_chunks) <= top_n and self.use_mock:
            return candidate_chunks[:top_n]

        self._load_model()

        if self.use_mock or self._model is None:
            # Fallback cross-scorer based on exact term matches + token overlap
            scored: List[Tuple[float, Dict[str, Any]]] = []
            query_tokens = set(re.findall(r"\w+", query.lower()))

            for item in candidate_chunks:
                payload = item.get("payload", {})
                content = payload.get("content", "").lower()
                symbol_name = (payload.get("symbol_name") or "").lower()

                # Score based on token overlap + symbol matching
                overlap = sum(1 for t in query_tokens if t in content)
                symbol_bonus = 2.0 if any(t in symbol_name for t in query_tokens) else 0.0
                score = (overlap + symbol_bonus) / (len(query_tokens) + 1e-5)
                item["rerank_score"] = float(score)
                scored.append((score, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:top_n]]

        # Use loaded Cross-Encoder
        pairs = [[query, c.get("payload", {}).get("content", "")] for c in candidate_chunks]
        try:
            scores = self._model.predict(pairs)
            for item, score in zip(candidate_chunks, scores):
                item["rerank_score"] = float(score)

            candidate_chunks.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return candidate_chunks[:top_n]
        except Exception:
            return candidate_chunks[:top_n]
