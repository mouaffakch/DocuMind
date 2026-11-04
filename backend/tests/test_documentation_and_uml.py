import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.code_file import CodeFile
from app.models.code_symbol import CodeSymbol, SymbolType
from app.models.dependency import SymbolDependency, DependencyType


@pytest.fixture
async def doc_test_project(db_session, test_user: User) -> Project:
    project = Project(
        owner_id=test_user.id,
        name="DocuMind Sample Core",
        repo_url="https://github.com/documind/sample-core",
        repo_full_name="documind/sample-core",
        description="Core sample library for documentation generation.",
        status=ProjectStatus.READY,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add code file
    cfile = CodeFile(
        project_id=project.id,
        file_path="src/order_service.py",
        language="python",
        size_bytes=300,
        sha256_hash="sha_order",
    )
    db_session.add(cfile)
    await db_session.flush()

    # Add symbols
    cls_sym = CodeSymbol(
        file_id=cfile.id,
        name="OrderService",
        symbol_type=SymbolType.CLASS,
        start_line=1,
        end_line=25,
        signature="class OrderService:",
        docstring="Manages customer orders and checkout.",
    )
    meth_sym = CodeSymbol(
        file_id=cfile.id,
        name="OrderService.process_order",
        symbol_type=SymbolType.METHOD,
        start_line=5,
        end_line=12,
        signature="def process_order(self, cart_id: str):",
    )
    db_session.add_all([cls_sym, meth_sym])
    await db_session.commit()
    return project


@pytest.mark.asyncio
async def test_generate_uml_class_diagram(
    async_client: AsyncClient,
    doc_test_project: Project,
    auth_headers: dict,
):
    proj_id = doc_test_project.id

    # 1. Generate UML Diagram
    payload = {
        "doc_type": "uml_diagram",
        "include_uml": True,
    }
    res = await async_client.post(
        f"/api/v1/projects/{proj_id}/documentation/generate",
        json=payload,
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert "Diagramme de Classes UML" in data["title"]
    assert "classDiagram" in data["mermaid_diagram"]
    assert "OrderService" in data["mermaid_diagram"]
    export_id = data["id"]

    # 2. Get Document by ID
    get_res = await async_client.get(
        f"/api/v1/projects/{proj_id}/documentation/{export_id}",
        headers=auth_headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == export_id

    # 3. List Documentation
    list_res = await async_client.get(
        f"/api/v1/projects/{proj_id}/documentation",
        headers=auth_headers,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Delete Document
    del_res = await async_client.delete(
        f"/api/v1/projects/{proj_id}/documentation/{export_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_generate_module_doc(
    async_client: AsyncClient,
    doc_test_project: Project,
    auth_headers: dict,
):
    proj_id = doc_test_project.id

    payload = {
        "doc_type": "module",
        "target_module": "order_service.py",
        "include_uml": False,
    }
    res = await async_client.post(
        f"/api/v1/projects/{proj_id}/documentation/generate",
        json=payload,
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert "order_service.py" in data["title"]
    assert "OrderService" in data["content_markdown"]
    assert "process_order" in data["content_markdown"]
