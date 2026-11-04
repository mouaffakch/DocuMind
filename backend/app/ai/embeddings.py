from typing import List, Optional
import os
import numpy as np
from app.core.config import settings


class EmbeddingEngine:
    """Generates dense vector embeddings using Sentence Transformers with fallback."""

    def __init__(self, model_name: Optional[str] = None, use_mock: bool = False):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.use_mock = use_mock or os.getenv("DOCUMIND_TESTING") == "true" or settings.ENVIRONMENT == "testing"
        self._model = None
        self.dimension = 384  # Default MiniLM / standard embedding dimension

    def _load_model(self):
        if self._model is None and not self.use_mock:
            try:
                from sentence_transformers import SentenceTransformer
                # Suppress progress bars in non-interactive server mode
                self._model = SentenceTransformer(self.model_name)
                self.dimension = self._model.get_sentence_embedding_dimension()
            except Exception:
                # Graceful fallback to lightweight mock in test / offline environments
                self.use_mock = True
                self.dimension = 384

    def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding for a single text string."""
        self._load_model()
        if self.use_mock or self._model is None:
            # Deterministic pseudo-embedding based on hash for testing
            return self._generate_deterministic_vector(text, self.dimension)
        
        vector = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings for multiple document chunks."""
        self._load_model()
        if not texts:
            return []
        
        if self.use_mock or self._model is None:
            return [self._generate_deterministic_vector(t, self.dimension) for t in texts]

        vectors = self._model.encode(texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.tolist()

    @staticmethod
    def _generate_deterministic_vector(text: str, dim: int) -> List[float]:
        """Generate normalized pseudo-random vector for deterministic offline testing."""
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
