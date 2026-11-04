import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.models.user import User
from app.schemas.project import GitHubRepoInfoResponse


@pytest.fixture
def mock_github_repo_info():
    """Sample GitHubRepoInfoResponse mock."""
    return GitHubRepoInfoResponse(
        owner="fastapi",
        repo_name="fastapi",
        full_name="fastapi/fastapi",
        description="FastAPI framework, high performance, easy to learn, fast to code, ready for production",
        default_branch="master",
        stars_count=75000,
        forks_count=6000,
        open_issues_count=120,
        is_private=False,
        clone_url="https://github.com/fastapi/fastapi.git",
        languages=["Python"],
    )


@pytest.mark.asyncio
async def test_inspect_github_repo(async_client: AsyncClient, auth_headers: dict, mock_github_repo_info):
    """Test inspecting a remote GitHub repository without importing it."""
    with patch("app.services.github_service.GitHubService.get_repo_metadata", return_value=mock_github_repo_info):
        response = await async_client.get(
            "/api/v1/projects/inspect?repo_url=https://github.com/fastapi/fastapi",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner"] == "fastapi"
        assert data["repo_name"] == "fastapi"
        assert data["default_branch"] == "master"
        assert "Python" in data["languages"]


@pytest.mark.asyncio
async def test_create_and_list_project(async_client: AsyncClient, auth_headers: dict, mock_github_repo_info):
    """Test importing a GitHub repository and listing user projects."""
    with patch("app.services.github_service.GitHubService.get_repo_metadata", return_value=mock_github_repo_info), \
         patch("app.services.github_service.GitHubService.get_latest_commit_sha", return_value="a1b2c3d4e5f67890"):
        
        # 1. Create Project
        payload = {
            "repo_url": "https://github.com/fastapi/fastapi",
            "name": "FastAPI Core",
        }
        res = await async_client.post("/api/v1/projects", json=payload, headers=auth_headers)
        assert res.status_code == 201
        created = res.json()
        assert created["name"] == "FastAPI Core"
        assert created["repo_full_name"] == "fastapi/fastapi"
        assert created["default_branch"] == "master"
        assert created["latest_commit_sha"] == "a1b2c3d4e5f67890"
        project_id = created["id"]

        # 2. List Projects
        list_res = await async_client.get("/api/v1/projects", headers=auth_headers)
        assert list_res.status_code == 200
        projects = list_res.json()
        assert len(projects) == 1
        assert projects[0]["id"] == project_id

        # 3. Get Project Details
        get_res = await async_client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "FastAPI Core"

        # 4. Trigger Sync
        sync_res = await async_client.post(f"/api/v1/projects/{project_id}/sync", headers=auth_headers)
        assert sync_res.status_code == 200
        assert sync_res.json()["status"] == "syncing"

        # 5. Delete Project
        del_res = await async_client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert del_res.status_code == 204

        # 6. Verify Project was Deleted
        get_after_del = await async_client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_project_import_fails(async_client: AsyncClient, auth_headers: dict, mock_github_repo_info):
    """Test importing the same repository twice returns 409 Conflict."""
    with patch("app.services.github_service.GitHubService.get_repo_metadata", return_value=mock_github_repo_info), \
         patch("app.services.github_service.GitHubService.get_latest_commit_sha", return_value="abc1234"):
        
        payload = {"repo_url": "https://github.com/fastapi/fastapi"}
        res1 = await async_client.post("/api/v1/projects", json=payload, headers=auth_headers)
        assert res1.status_code == 201

        # Second attempt must return 409
        res2 = await async_client.post("/api/v1/projects", json=payload, headers=auth_headers)
        assert res2.status_code == 409
        assert "déjà été importé" in res2.json()["message"]
