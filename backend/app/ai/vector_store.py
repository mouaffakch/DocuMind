from typing import List, Dict, Any, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import settings
from app.ingestion.chunker import CodeChunk


class QdrantVectorStore:
    """Interface to Qdrant vector database with metadata filtering and resilient fallback."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
        vector_size: int = 384,
        force_in_memory: bool = False,
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_size = vector_size

        if force_in_memory:
            self.client = QdrantClient(":memory:")
        else:
            try:
                # Try connecting to remote Qdrant container
                self.client = QdrantClient(
                    host=host or settings.QDRANT_HOST,
                    port=port or settings.QDRANT_PORT,
                    timeout=1.0,
                )
                self.client.get_collections()
            except Exception:
                # Fallback to local memory mode for standalone development / testing
                self.client = QdrantClient(":memory:")

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """Create the collection with HNSW index if it doesn't already exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def upsert_chunks(
        self,
        project_id: UUID,
        chunks: List[CodeChunk],
        vectors: List[List[float]],
        commit_sha: Optional[str] = None,
    ) -> None:
        """Upsert embedded code chunks into Qdrant with project payload filtering."""
        if not chunks or not vectors or len(chunks) != len(vectors):
            return

        points: List[PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            payload = {
                "project_id": str(project_id),
                "file_path": chunk.file_path,
                "language": chunk.language,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
                "symbol_name": chunk.symbol_name,
                "symbol_type": chunk.symbol_type,
                "commit_sha": commit_sha or "latest",
            }
            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search_similar(
        self,
        project_id: UUID,
        query_vector: List[float],
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Perform dense semantic search restricted to a single project using modern query_points."""
        project_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=str(project_id)),
                )
            ]
        )

        try:
            # Modern Qdrant client 1.10+ uses query_points
            query_res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=project_filter,
                limit=limit,
                with_payload=True,
            )
            points = query_res.points
        except Exception:
            return []

        hits: List[Dict[str, Any]] = []
        for r in points:
            hits.append(
                {
                    "id": r.id,
                    "score": float(r.score) if hasattr(r, "score") and r.score is not None else 0.0,
                    "payload": r.payload or {},
                }
            )
        return hits

    def delete_project_vectors(self, project_id: UUID) -> None:
        """Purge all chunks associated with a project."""
        project_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=str(project_id)),
                )
            ]
        )
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=project_filter,
            )
        except Exception:
            pass
