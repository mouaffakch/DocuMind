import os
import tempfile
import pytest
from httpx import AsyncClient
from app.main import app
from app.api.deps import get_chat_service, get_db_session
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.ingestion_service import IngestionService
from app.services.chat_service import ChatService
from app.ai.embeddings import EmbeddingEngine
from app.ai.vector_store import QdrantVectorStore
from app.ai.reranker import CrossEncoderReranker
from app.ai.rag_pipeline import RAGPipeline


@pytest.fixture
def mock_vstore():
    """Shared in-memory Qdrant store for test."""
    return QdrantVectorStore(force_in_memory=True, vector_size=384)


@pytest.fixture
async def indexed_project(db_session, test_user: User, mock_vstore) -> Project:
    """Fixture creating an indexed project with sample Python code in-memory."""
    project = Project(
        owner_id=test_user.id,
        name="Sample Project",
        repo_url="https://github.com/documind/sample",
        repo_full_name="documind/sample",
        default_branch="main",
        status=ProjectStatus.READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Ingest a temporary directory containing code
    with tempfile.TemporaryDirectory() as tmp_dir:
        auth_file = os.path.join(tmp_dir, "auth_service.py")
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write(
                "class JWTValidator:\n"
                "    def validate_token(self, token: str) -> bool:\n"
                "        \"\"\"Verify JWT signature.\"\"\"\n"
                "        return token.startswith('valid_')\n"
            )

        embedder = EmbeddingEngine(use_mock=True)
        ingestion_service = IngestionService(
            session=db_session,
            vector_store=mock_vstore,
            embedder=embedder,
        )
        await ingestion_service.ingest_project(project.id, test_user, local_source_dir=tmp_dir)

    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_chat_lifecycle_with_rag(
    async_client: AsyncClient, 
    test_user: User, 
    indexed_project: Project, 
    auth_headers: dict,
    db_session,
    mock_vstore,
):
    """Test full chat session creation, question asking, RAG grounded citations and history."""
    proj_id = indexed_project.id

    # Inject mock RAG pipeline into ChatService for testing
    embedder = EmbeddingEngine(use_mock=True)
    rag_pipe = RAGPipeline(
        vector_store=mock_vstore,
        embedder=embedder,
        reranker=CrossEncoderReranker(use_mock=True),
    )
    test_chat_service = ChatService(session=db_session, rag_pipeline=rag_pipe)

    app.dependency_overrides[get_chat_service] = lambda: test_chat_service

    try:
        # 1. Create Chat Session
        sess_res = await async_client.post(
            f"/api/v1/projects/{proj_id}/chat/sessions",
            json={"title": "Questions sur l'authentification"},
            headers=auth_headers,
        )
        assert sess_res.status_code == 201
        session_data = sess_res.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Questions sur l'authentification"

        # 2. Ask Question (Synchronous)
        question_payload = {"content": "Où se trouve la fonction responsable de la validation du JWT ?"}
        ask_res = await async_client.post(
            f"/api/v1/projects/{proj_id}/chat/sessions/{session_id}/messages",
            json=question_payload,
            headers=auth_headers,
        )
        assert ask_res.status_code == 200
        msg_data = ask_res.json()
        assert msg_data["role"] == "assistant"
        assert "content" in msg_data
        assert len(msg_data["citations"]) >= 1
        assert msg_data["citations"][0]["file_path"] == "auth_service.py"

        # 3. List Sessions
        list_res = await async_client.get(
            f"/api/v1/projects/{proj_id}/chat/sessions",
            headers=auth_headers,
        )
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 4. Get Session History
        hist_res = await async_client.get(
            f"/api/v1/projects/{proj_id}/chat/sessions/{session_id}/messages",
            headers=auth_headers,
        )
        assert hist_res.status_code == 200
        messages = hist_res.json()
        assert len(messages) >= 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        # 5. Test SSE Streaming Question
        stream_res = await async_client.post(
            f"/api/v1/projects/{proj_id}/chat/sessions/{session_id}/messages/stream",
            json={"content": "Explique le fonctionnement de JWTValidator"},
            headers=auth_headers,
        )
        assert stream_res.status_code == 200
        assert "text/event-stream" in stream_res.headers["content-type"]
        assert "data:" in stream_res.text

        # 6. Delete Session
        del_res = await async_client.delete(
            f"/api/v1/projects/{proj_id}/chat/sessions/{session_id}",
            headers=auth_headers,
        )
        assert del_res.status_code == 204
    finally:
        app.dependency_overrides.pop(get_chat_service, None)
