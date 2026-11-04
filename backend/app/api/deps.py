from typing import AsyncGenerator, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.ingestion_service import IngestionService
from app.services.chat_service import ChatService
from app.services.impact_service import ImpactService
from app.services.bug_analysis_service import BugAnalysisService
from app.services.doc_service import DocService

# OAuth2 scheme for Swagger UI Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Dependency providing AuthService."""
    return AuthService(session)


def get_project_service(
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> ProjectService:
    """Dependency providing ProjectService."""
    return ProjectService(session, auth_service=auth_service)


def get_ingestion_service(
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> IngestionService:
    """Dependency providing IngestionService."""
    return IngestionService(session, auth_service=auth_service)


def get_chat_service(
    session: AsyncSession = Depends(get_db_session),
) -> ChatService:
    """Dependency providing ChatService."""
    return ChatService(session)


def get_impact_service(
    session: AsyncSession = Depends(get_db_session),
) -> ImpactService:
    """Dependency providing ImpactService."""
    return ImpactService(session)


def get_bug_analysis_service(
    session: AsyncSession = Depends(get_db_session),
) -> BugAnalysisService:
    """Dependency providing BugAnalysisService."""
    return BugAnalysisService(session)


def get_doc_service(
    session: AsyncSession = Depends(get_db_session),
) -> DocService:
    """Dependency providing DocService."""
    return DocService(session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency extracting the authenticated user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton d'authentification invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte utilisateur est inactif.",
        )

    return user


def require_roles(allowed_roles: List[UserRole]):
    """Role-Based Access Control (RBAC) dependency factory."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions insuffisantes pour effectuer cette opération.",
            )
        return current_user
    return role_checker
