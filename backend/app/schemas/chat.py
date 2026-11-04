from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.chat import MessageRole


class CitationResponse(BaseModel):
    id: UUID
    file_path: str
    start_line: int
    end_line: int
    relevance_score: float
    code_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Question or prompt from user")


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    execution_time_seconds: float
    citations: List[CitationResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreateRequest(BaseModel):
    title: Optional[str] = Field("Nouvelle conversation", max_length=150)


class ChatSessionResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages_count: int = 0

    model_config = ConfigDict(from_attributes=True)
