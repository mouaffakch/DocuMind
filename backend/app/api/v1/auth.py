from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserUpdateRequest,
    UserGitHubTokenRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
)
async def register(
    data: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account."""
    user = await auth_service.register(data)
    return auth_service.to_user_response(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login (JSON / Form)",
)
async def login(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with username (email) and password via JSON body or form-data."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            username, password = None, None
    else:
        try:
            form = await request.form()
            username = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            username, password = None, None

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifiants (email et mot de passe) requis.",
        )
    return await auth_service.authenticate(str(username), str(password))


@router.post(
    "/login/json",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login (JSON Body)",
)
async def login_json(
    data: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with JSON body to receive JWT tokens."""
    return await auth_service.authenticate(data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Obtain a new access token using a valid refresh token."""
    return await auth_service.refresh_access_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Retrieve profile and settings of the authenticated user."""
    return auth_service.to_user_response(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
)
async def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Update profile details for the authenticated user."""
    user = await auth_service.update_profile(current_user, data)
    return auth_service.to_user_response(user)


@router.put(
    "/github-token",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Save GitHub Personal Access Token",
)
async def save_github_token(
    data: UserGitHubTokenRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Securely encrypt and store a GitHub PAT for private repos and higher rate limits."""
    user = await auth_service.set_github_pat(current_user, data.github_pat)
    return auth_service.to_user_response(user)


@router.delete(
    "/github-token",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove GitHub Personal Access Token",
)
async def remove_github_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Remove stored GitHub PAT from account."""
    user = await auth_service.remove_github_pat(current_user)
    return auth_service.to_user_response(user)
