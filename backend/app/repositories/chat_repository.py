from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.chat import ChatSession, ChatMessage, Citation
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    """Repository handling database operations for chat sessions and messages."""

    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def list_by_project_and_user(self, project_id: UUID, user_id: UUID) -> List[ChatSession]:
        """Fetch all chat sessions for a specific project and user, newest first."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.project_id == project_id, ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_session_with_messages(self, session_id: UUID, user_id: UUID) -> Optional[ChatSession]:
        """Fetch a session along with its messages and citations."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(
                selectinload(ChatSession.messages).selectinload(ChatMessage.citations)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_message_with_citations(
        self,
        session_id: UUID,
        role: str,
        content: str,
        execution_time: float,
        citations: List[Citation],
    ) -> ChatMessage:
        """Persist a chat message and its associated code citations."""
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            execution_time_seconds=execution_time,
        )
        self.session.add(msg)
        await self.session.flush()

        for c in citations:
            c.message_id = msg.id
            self.session.add(c)

        await self.session.flush()
        await self.session.refresh(msg)
        return msg
