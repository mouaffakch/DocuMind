import enum
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(BaseModel):
    """Represents a conversation thread within a project."""
    __tablename__ = "chat_sessions"

    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="Nouvelle conversation", nullable=False)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at", lazy="selectin")


class ChatMessage(BaseModel):
    """Represents an individual message exchanged in a chat session."""
    __tablename__ = "chat_messages"

    session_id = Column(Uuid(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    execution_time_seconds = Column(Float, default=0.0, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan", lazy="selectin")


class Citation(BaseModel):
    """Represents a verifiable source code citation linked to an assistant answer."""
    __tablename__ = "citations"

    message_id = Column(Uuid(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1024), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    code_snippet = Column(Text, nullable=True)

    # Relationships
    message = relationship("ChatMessage", back_populates="citations")
