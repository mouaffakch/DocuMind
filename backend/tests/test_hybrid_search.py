import uuid
import pytest
from app.ai.embeddings import EmbeddingEngine
from app.ai.vector_store import QdrantVectorStore
from app.ai.hybrid_search import HybridSearchEngine, CodeTokenizer
from app.ai.reranker import CrossEncoderReranker
from app.ingestion.chunker import CodeChunk


def test_code_tokenizer_handles_camel_and_snake_case():
    text = "def authenticateUser_v2(jwtToken: str, db_connection):"
    tokens = CodeTokenizer.tokenize(text)
    assert "authenticate" in tokens
    assert "user" in tokens
    assert "jwt" in tokens
    assert "token" in tokens
    assert "db" in tokens
    assert "connection" in tokens


def test_qdrant_vector_store_in_memory():
    store = QdrantVectorStore(force_in_memory=True, vector_size=384)
    project_id = uuid.uuid4()

    chunks = [
        CodeChunk(
            chunk_id=str(uuid.uuid4()),
            file_path="src/auth.py",
            language="python",
            start_line=1,
            end_line=15,
            content="def verify_jwt(token: str) -> bool: return True",
            symbol_name="verify_jwt",
            symbol_type="function",
        )
    ]
    embedder = EmbeddingEngine(use_mock=True)
    vectors = embedder.embed_documents([c.content for c in chunks])

    store.upsert_chunks(project_id, chunks, vectors)

    # Search with same text
    q_vec = embedder.embed_text("verify_jwt")
    results = store.search_similar(project_id, q_vec, limit=5)

    assert len(results) == 1
    assert results[0]["payload"]["file_path"] == "src/auth.py"
    assert results[0]["payload"]["symbol_name"] == "verify_jwt"


def test_hybrid_search_and_reranking():
    store = QdrantVectorStore(force_in_memory=True, vector_size=384)
    embedder = EmbeddingEngine(use_mock=True)
    hybrid_engine = HybridSearchEngine(store, embedder)
    reranker = CrossEncoderReranker(use_mock=True)
    project_id = uuid.uuid4()

    chunk1 = CodeChunk(
        chunk_id=str(uuid.uuid4()),
        file_path="src/payment.py",
        language="python",
        start_line=1,
        end_line=20,
        content="def process_stripe_payment(amount: int, currency: str): pass",
        symbol_name="process_stripe_payment",
        symbol_type="function",
    )
    chunk2 = CodeChunk(
        chunk_id=str(uuid.uuid4()),
        file_path="src/auth.py",
        language="python",
        start_line=1,
        end_line=20,
        content="def authenticate_user(username: str, password_hash: str): pass",
        symbol_name="authenticate_user",
        symbol_type="function",
    )

    chunks = [chunk1, chunk2]
    vectors = embedder.embed_documents([c.content for c in chunks])
    store.upsert_chunks(project_id, chunks, vectors)

    corpus = [
        {
            "chunk_id": c.chunk_id,
            "content": c.content,
            "file_path": c.file_path,
            "symbol_name": c.symbol_name,
            "start_line": c.start_line,
            "end_line": c.end_line,
        }
        for c in chunks
    ]

    fused = hybrid_engine.search(
        project_id=project_id,
        query="process_stripe_payment",
        corpus_chunks=corpus,
        top_k=5,
    )
    assert len(fused) == 2
    # Rerank to top 1
    top_ranked = reranker.rerank(query="process_stripe_payment", candidate_chunks=fused, top_n=1)
    assert len(top_ranked) == 1
    assert top_ranked[0]["payload"]["symbol_name"] == "process_stripe_payment"
