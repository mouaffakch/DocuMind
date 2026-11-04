import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "email": "alice@documind.io",
        "password": "Password12345!",
        "full_name": "Alice Developer",
        "role": "developer",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@documind.io"
    assert data["full_name"] == "Alice Developer"
    assert data["role"] == "developer"
    assert data["is_active"] is True
    assert data["has_github_pat"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client: AsyncClient, test_user: User):
    """Test that registering an existing email returns 409 Conflict."""
    payload = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "existe déjà" in response.json()["message"]


@pytest.mark.asyncio
async def test_login_json_success(async_client: AsyncClient, test_user: User):
    """Test login via JSON payload returns JWT access and refresh tokens."""
    payload = {
        "email": test_user.email,
        "password": "SuperSecret123!",
    }
    response = await async_client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, test_user: User):
    """Test login with incorrect password returns 401 Unauthorized."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword!",
    }
    response = await async_client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test retrieving authenticated user profile."""
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_unauthorized_access_without_token(async_client: AsyncClient):
    """Test that accessing protected endpoint without token returns 401."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient, test_user: User):
    """Test exchanging refresh token for a new access token."""
    login_res = await async_client.post(
        "/api/v1/auth/login/json",
        json={"email": test_user.email, "password": "SuperSecret123!"},
    )
    tokens = login_res.json()
    refresh_token = tokens["refresh_token"]

    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


@pytest.mark.asyncio
async def test_github_pat_lifecycle(async_client: AsyncClient, auth_headers: dict):
    """Test setting, verifying and removing encrypted GitHub PAT."""
    # 1. Save PAT
    pat_payload = {"github_pat": "ghp_MockSecretPersonalAccessToken12345"}
    save_res = await async_client.put("/api/v1/auth/github-token", json=pat_payload, headers=auth_headers)
    assert save_res.status_code == 200
    assert save_res.json()["has_github_pat"] is True

    # 2. Check profile reflects PAT presence
    me_res = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.json()["has_github_pat"] is True

    # 3. Delete PAT
    del_res = await async_client.delete("/api/v1/auth/github-token", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["has_github_pat"] is False
