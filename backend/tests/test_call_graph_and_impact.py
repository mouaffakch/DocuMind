import uuid
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.code_file import CodeFile
from app.models.code_symbol import CodeSymbol, SymbolType
from app.models.dependency import SymbolDependency, DependencyType
from app.ingestion.call_graph_extractor import CallGraphExtractor


def test_call_graph_extractor_python():
    code = """
def authenticate_user(token: str) -> bool:
    return len(token) > 5

def handle_login_request(req):
    valid = authenticate_user(req.token)
    return valid
"""
    deps = CallGraphExtractor.extract_dependencies(code, "python", "src/auth.py")
    assert len(deps) == 1
    dep = deps[0]
    assert dep.caller_name == "handle_login_request"
    assert dep.callee_name == "authenticate_user"
    assert dep.caller_file_path == "src/auth.py"
    assert dep.caller_line == 6


@pytest.fixture
async def impact_test_project(db_session, test_user: User) -> Project:
    project = Project(
        owner_id=test_user.id,
        name="Impact Demo Project",
        repo_url="https://github.com/documind/impact-demo",
        repo_full_name="documind/impact-demo",
        status=ProjectStatus.READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 1. Add CodeFile and target Symbol
    code_file = CodeFile(
        project_id=project.id,
        file_path="src/security/auth.py",
        language="python",
        size_bytes=500,
        sha256_hash="hash123",
    )
    db_session.add(code_file)
    await db_session.flush()

    target_sym = CodeSymbol(
        file_id=code_file.id,
        name="authenticate_user",
        symbol_type=SymbolType.FUNCTION,
        start_line=15,
        end_line=30,
        signature="def authenticate_user(username: str, password: str):",
    )
    db_session.add(target_sym)

    # 2. Add Direct Caller (Service)
    dep1 = SymbolDependency(
        project_id=project.id,
        caller_name="login_controller",
        caller_file_path="src/api/routes.py",
        caller_line=45,
        callee_name="authenticate_user",
        dependency_type=DependencyType.CALL,
    )
    # 3. Add Transitive Caller
    dep2 = SymbolDependency(
        project_id=project.id,
        caller_name="main_app",
        caller_file_path="src/main.py",
        caller_line=12,
        callee_name="login_controller",
        dependency_type=DependencyType.CALL,
    )
    # 4. Add Test Caller
    dep3 = SymbolDependency(
        project_id=project.id,
        caller_name="test_auth_success",
        caller_file_path="tests/test_auth.py",
        caller_line=20,
        callee_name="authenticate_user",
        dependency_type=DependencyType.CALL,
    )

    db_session.add_all([dep1, dep2, dep3])
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_impact_analysis_endpoint(
    async_client: AsyncClient,
    impact_test_project: Project,
    auth_headers: dict,
):
    proj_id = impact_test_project.id

    # 1. Call Impact Analysis
    res = await async_client.get(
        f"/api/v1/projects/{proj_id}/impact?symbol_name=authenticate_user&max_depth=3",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["target_symbol"] == "authenticate_user"
    assert data["target_file"] == "src/security/auth.py"
    assert data["target_line"] == 15

    # Check Nodes and Edges
    node_labels = [n["label"] for n in data["nodes"]]
    assert "authenticate_user" in node_labels
    assert "login_controller" in node_labels
    assert "test_auth_success" in node_labels
    assert "main_app" in node_labels

    # Check affected test detection
    assert "tests/test_auth.py" in data["affected_tests"]

    # Check impacted files
    assert "src/api/routes.py" in data["impacted_files"]
    assert "src/main.py" in data["impacted_files"]

    # Check risk assessment
    risk = data["risk_assessment"]
    assert risk["direct_callers_count"] == 2  # login_controller + test_auth_success
    assert risk["transitive_callers_count"] == 1  # main_app
    assert risk["level"] in ("MEDIUM", "HIGH", "CRITICAL")
    assert "composants" in risk["explanation"] or "dépendent" in risk["explanation"]


@pytest.mark.asyncio
async def test_symbol_autocomplete_endpoint(
    async_client: AsyncClient,
    impact_test_project: Project,
    auth_headers: dict,
):
    proj_id = impact_test_project.id

    res = await async_client.get(
        f"/api/v1/projects/{proj_id}/impact/symbols?query=auth",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["name"] == "authenticate_user"
    assert data[0]["file_path"] == "src/security/auth.py"
