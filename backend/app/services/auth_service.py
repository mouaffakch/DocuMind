from typing import Optional
from uuid import UUID
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserRegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_secret,
    decrypt_secret,
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    EntityNotFoundError,
)


class AuthService:
    """Service handling user authentication, profile updates, and JWT issuance."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserRegisterRequest) -> User:
        """Register a new user account."""
        if await self.user_repo.exists_by_email(data.email):
            raise ConflictError(f"Un compte avec l'adresse email '{data.email}' existe déjà.")

        user = User(
            email=data.email.strip().lower(),
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name.strip(),
            role=data.role or UserRole.DEVELOPER,
            is_active=True,
        )
        return await self.user_repo.create(user)

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        """Validate credentials and issue JWT tokens."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Adresse email ou mot de passe incorrect.")

        if not user.is_active:
            raise AuthenticationError("Ce compte utilisateur est désactivé.")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Generate a new access token from a valid refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Jeton de rafraîchissement invalide ou expiré.")

        user_id_str = payload.get("sub")
        try:
            user_id = UUID(user_id_str)
        except (ValueError, TypeError):
            raise AuthenticationError("Identifiant utilisateur invalide dans le jeton.")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Utilisateur introuvable ou compte désactivé.")

        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def update_profile(self, user: User, data: UserUpdateRequest) -> User:
        """Update user profile info."""
        if data.full_name:
            user.full_name = data.full_name.strip()
        if data.email and data.email.strip().lower() != user.email:
            if await self.user_repo.exists_by_email(data.email):
                raise ConflictError(f"L'adresse email '{data.email}' est déjà utilisée.")
            user.email = data.email.strip().lower()

        return await self.user_repo.update(user)

    async def set_github_pat(self, user: User, pat: str) -> User:
        """Encrypt and store user's GitHub Personal Access Token."""
        user.github_pat_encrypted = encrypt_secret(pat.strip())
        return await self.user_repo.update(user)

    async def remove_github_pat(self, user: User) -> User:
        """Clear user's stored GitHub PAT."""
        user.github_pat_encrypted = None
        return await self.user_repo.update(user)

    def get_decrypted_pat(self, user: User) -> Optional[str]:
        """Decrypt the stored GitHub PAT for internal use."""
        if not user.github_pat_encrypted:
            return None
        try:
            return decrypt_secret(user.github_pat_encrypted)
        except Exception:
            return None

    def to_user_response(self, user: User) -> UserResponse:
        """Convert a User entity to UserResponse DTO with computed properties."""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            has_github_pat=bool(user.github_pat_encrypted),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
