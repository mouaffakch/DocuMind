import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.bug_analysis_service import BugAnalysisService


def test_stacktrace_extractor():
    stacktrace = """
Traceback (most recent call last):
  File "app/services/auth_service.py", line 42, in authenticate
    return verify_token(token)
  File "app/core/security.py", line 18, in verify_token
    raise JWTError("Invalid signature")
jwt.exceptions.JWTError: Invalid signature
"""
    hints = BugAnalysisService.extract_stacktrace_files_and_lines(stacktrace)
    assert len(hints) == 2
    assert hints[0]["file"] == "app/services/auth_service.py"
    assert hints[0]["line"] == 42
    assert hints[0]["func"] == "authenticate"
    assert hints[1]["file"] == "app/core/security.py"
    assert hints[1]["line"] == 18


@pytest.fixture
async def bug_test_project(db_session, test_user: User) -> Project:
    project = Project(
        owner_id=test_user.id,
        name="Bug Test Project",
        repo_url="https://github.com/documind/bug-demo",
        repo_full_name="documind/bug-demo",
        status=ProjectStatus.READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_bug_analysis_endpoint(
    async_client: AsyncClient,
    bug_test_project: Project,
    auth_headers: dict,
):
    proj_id = bug_test_project.id

    payload = {
        "title": "JWT Signature Verification Failure",
        "description": "Users are randomly logged out with a 401 error during token refresh.",
        "stacktrace": 'File "src/auth/jwt.py", line 55, in verify_jwt_token\n  raise JWTError("Signature expired")',
    }

    res = await async_client.post(
        f"/api/v1/projects/{proj_id}/bug-analysis",
        json=payload,
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()

    assert "Diagnostic" in data["problem_summary"]
    assert len(data["hypothetical_causes"]) >= 1
    assert any("cause" in c.lower() or "hypothèse" in c.lower() for c in data["hypothetical_causes"])
    assert len(data["suggested_fixes"]) >= 1
    assert len(data["recommended_tests"]) >= 1
