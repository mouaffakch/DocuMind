import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.project import Project
from app.models.chat import ChatSession, ChatMessage, Citation, MessageRole
from app.models.code_file import CodeFile
from app.repositories.chat_repository import ChatRepository
from app.repositories.project_repository import ProjectRepository
from app.ai.rag_pipeline import RAGPipeline
from app.schemas.chat import (
    ChatSessionResponse,
    ChatMessageResponse,
    CitationResponse,
)
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError


class ChatService:
    """Service orchestrating chat sessions, RAG queries, and SSE streaming responses."""

    def __init__(
        self,
        session: AsyncSession,
        rag_pipeline: Optional[RAGPipeline] = None,
    ):
        self.session = session
        self.chat_repo = ChatRepository(session)
        self.project_repo = ProjectRepository(session)
        self.rag_pipeline = rag_pipeline or RAGPipeline()

    async def create_session(
        self,
        user: User,
        project_id: UUID,
        title: Optional[str] = None,
    ) -> ChatSession:
        """Create a new chat conversation thread for a project."""
        project = await self.project_repo.get_by_owner_and_id(user.id, project_id)
        if not project:
            raise EntityNotFoundError(f"Projet introuvable ({project_id}).")

        new_session = ChatSession(
            project_id=project_id,
            user_id=user.id,
            title=title or "Nouvelle conversation",
        )
        return await self.chat_repo.create(new_session)

    async def list_sessions(self, user: User, project_id: UUID) -> List[ChatSessionResponse]:
        """List all conversation threads in a project for the user."""
        sessions = await self.chat_repo.list_by_project_and_user(project_id, user.id)
        return [
            ChatSessionResponse(
                id=s.id,
                project_id=s.project_id,
                user_id=s.user_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                messages_count=0,
            )
            for s in sessions
        ]

    async def get_session_history(self, user: User, session_id: UUID) -> List[ChatMessageResponse]:
        """Fetch all messages and citations in a session."""
        chat_session = await self.chat_repo.get_session_with_messages(session_id, user.id)
        if not chat_session:
            raise EntityNotFoundError(f"Session de conversation introuvable ({session_id}).")

        responses: List[ChatMessageResponse] = []
        for msg in chat_session.messages:
            citations_dto = [
                CitationResponse(
                    id=c.id,
                    file_path=c.file_path,
                    start_line=c.start_line,
                    end_line=c.end_line,
                    relevance_score=c.relevance_score,
                    code_snippet=c.code_snippet,
                )
                for c in msg.citations
            ]
            responses.append(
                ChatMessageResponse(
                    id=msg.id,
                    session_id=msg.session_id,
                    role=msg.role,
                    content=msg.content,
                    execution_time_seconds=msg.execution_time_seconds,
                    citations=citations_dto,
                    created_at=msg.created_at,
                )
            )
        return responses

    async def delete_session(self, user: User, session_id: UUID) -> None:
        """Delete a conversation session."""
        chat_session = await self.chat_repo.get_by_id(session_id)
        if not chat_session or chat_session.user_id != user.id:
            raise EntityNotFoundError("Session introuvable.")
        await self.chat_repo.delete(chat_session)

    async def ask_question(
        self,
        user: User,
        session_id: UUID,
        query: str,
    ) -> ChatMessageResponse:
        """Synchronously process a user prompt through the RAG pipeline."""
        chat_session = await self.chat_repo.get_session_with_messages(session_id, user.id)
        if not chat_session:
            raise EntityNotFoundError(f"Session introuvable ({session_id}).")

        # 1. Save user question message
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=query,
            execution_time_seconds=0.0,
        )
        self.session.add(user_msg)
        await self.session.flush()

        # Update session title if default
        if chat_session.title == "Nouvelle conversation":
            chat_session.title = query[:40] + ("..." if len(query) > 40 else "")
            await self.chat_repo.update(chat_session)

        # Build history context
        history = [
            {"role": m.role.value, "content": m.content}
            for m in chat_session.messages[-6:]
        ]

        # 2. Run RAG Pipeline
        rag_output = await self.rag_pipeline.execute(
            project_id=chat_session.project_id,
            query=query,
            corpus_chunks=[],  # Will query Qdrant & local BM25
            conversation_history=history,
        )

        # 3. Save assistant message and citations
        citation_entities = [
            Citation(
                file_path=c.file_path,
                start_line=c.start_line,
                end_line=c.end_line,
                relevance_score=c.relevance_score,
                code_snippet=c.code_snippet,
            )
            for c in rag_output.citations
        ]

        assistant_msg = await self.chat_repo.add_message_with_citations(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=rag_output.content,
            execution_time=rag_output.execution_time_seconds,
            citations=citation_entities,
        )

        citations_dto = [
            CitationResponse(
                id=c.id,
                file_path=c.file_path,
                start_line=c.start_line,
                end_line=c.end_line,
                relevance_score=c.relevance_score,
                code_snippet=c.code_snippet,
            )
            for c in citation_entities
        ]

        return ChatMessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            execution_time_seconds=assistant_msg.execution_time_seconds,
            citations=citations_dto,
            created_at=assistant_msg.created_at,
        )

    async def stream_question(
        self,
        user: User,
        session_id: UUID,
        query: str,
    ) -> AsyncGenerator[str, None]:
        """Stream RAG response tokens via Server-Sent Events (SSE)."""
        chat_session = await self.chat_repo.get_session_with_messages(session_id, user.id)
        if not chat_session:
            yield f"data: {json.dumps({'error': 'Session introuvable'})}\n\n"
            return

        # Execute RAG
        rag_output = await self.rag_pipeline.execute(
            project_id=chat_session.project_id,
            query=query,
            corpus_chunks=[],
        )

        # Stream tokens
        words = rag_output.content.split(" ")
        for i in range(0, len(words), 3):
            token = " ".join(words[i : i + 3]) + (" " if i + 3 < len(words) else "")
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

        # Save assistant message
        citation_entities = [
            Citation(
                file_path=c.file_path,
                start_line=c.start_line,
                end_line=c.end_line,
                relevance_score=c.relevance_score,
                code_snippet=c.code_snippet,
            )
            for c in rag_output.citations
        ]

        assistant_msg = await self.chat_repo.add_message_with_citations(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=rag_output.content,
            execution_time=rag_output.execution_time_seconds,
            citations=citation_entities,
        )

        # Yield completion payload with citations
        citations_payload = [
            {
                "file_path": c.file_path,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "relevance_score": c.relevance_score,
                "code_snippet": c.code_snippet,
            }
            for c in rag_output.citations
        ]
        yield f"data: {json.dumps({'token': '', 'done': True, 'citations': citations_payload})}\n\n"
