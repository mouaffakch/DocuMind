from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatMessageCreateRequest,
    ChatMessageResponse,
)
from app.services.chat_service import ChatService
from app.api.deps import get_chat_service, get_current_user

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["AI Chatbot"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Chat Session",
)
async def create_session(
    project_id: UUID,
    data: ChatSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatSessionResponse:
    """Create a new conversational thread for a specific project."""
    session = await chat_service.create_session(current_user, project_id, title=data.title)
    return ChatSessionResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Chat Sessions",
)
async def list_sessions(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> List[ChatSessionResponse]:
    """List all conversation threads associated with a project."""
    return await chat_service.list_sessions(current_user, project_id)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Chat History",
)
async def get_session_messages(
    project_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> List[ChatMessageResponse]:
    """Retrieve full conversation history and source citations for a session."""
    return await chat_service.get_session_history(current_user, session_id)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Chat Session",
)
async def delete_session(
    project_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a conversation thread."""
    await chat_service.delete_session(current_user, session_id)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Question (Synchronous)",
)
async def ask_question(
    project_id: UUID,
    session_id: UUID,
    data: ChatMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatMessageResponse:
    """Ask a question about the repository code and receive a grounded response with citations."""
    return await chat_service.ask_question(current_user, session_id, query=data.content)


@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="Ask Question (SSE Streaming)",
)
async def stream_question(
    project_id: UUID,
    session_id: UUID,
    data: ChatMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Ask a question and receive real-time streamed tokens via Server-Sent Events (SSE)."""
    generator = chat_service.stream_question(current_user, session_id, query=data.content)
    return StreamingResponse(generator, media_type="text/event-stream")
