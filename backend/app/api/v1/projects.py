from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, BackgroundTasks

from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectSyncResponse,
    GitHubRepoInfoResponse,
)
from app.schemas.ingestion import (
    CodeFileResponse,
    CodeSymbolResponse,
    IngestionProgressResponse,
)
from app.services.project_service import ProjectService
from app.services.github_service import GitHubService
from app.services.auth_service import AuthService
from app.services.ingestion_service import IngestionService
from app.api.deps import (
    get_project_service,
    get_auth_service,
    get_ingestion_service,
    get_current_user,
)

router = APIRouter(prefix="/projects", tags=["Projects & Repositories"])


@router.get(
    "/inspect",
    response_model=GitHubRepoInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect Remote GitHub Repository",
)
async def inspect_github_repo(
    repo_url: str = Query(..., description="GitHub repository URL or 'owner/repo'"),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> GitHubRepoInfoResponse:
    """Inspect repository metadata (stars, description, default branch, languages) before import."""
    owner, repo = GitHubService.parse_repo_url(repo_url)
    pat = auth_service.get_decrypted_pat(current_user)
    return await GitHubService.get_repo_metadata(owner, repo, pat=pat)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import GitHub Repository as Project",
)
async def create_project(
    data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Import a new GitHub repository into the user's workspace."""
    project = await project_service.create_project(current_user, data)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Projects",
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> List[ProjectResponse]:
    """Retrieve all projects imported by the current user."""
    projects = await project_service.list_user_projects(current_user)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Get metadata and indexing statistics for a specific project."""
    project = await project_service.get_project(current_user, project_id)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project and all associated files and vectors."""
    await project_service.delete_project(current_user, project_id)


@router.post(
    "/{project_id}/sync",
    response_model=ProjectSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Project Synchronization",
)
async def sync_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectSyncResponse:
    """Trigger a synchronisation of the project with its remote GitHub repository."""
    return await project_service.trigger_sync(current_user, project_id)


@router.post(
    "/{project_id}/ingest",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Project Ingestion & AST RAG Indexing",
)
async def ingest_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> ProjectResponse:
    """Run full AST parsing, chunking, embedding and Qdrant indexing for the project."""
    updated_project = await ingestion_service.ingest_project(project_id, current_user)
    return ProjectResponse.model_validate(updated_project)


@router.get(
    "/{project_id}/files",
    response_model=List[CodeFileResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Code Files",
)
async def list_project_files(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> List[CodeFileResponse]:
    """List all indexed code and markdown files for this project."""
    files = await ingestion_service.list_project_files(project_id, current_user)
    return [
        CodeFileResponse(
            id=f.id,
            project_id=f.project_id,
            file_path=f.file_path,
            language=f.language,
            size_bytes=f.size_bytes,
            sha256_hash=f.sha256_hash,
            symbols_count=0,
            created_at=f.created_at,
        )
        for f in files
    ]


@router.get(
    "/{project_id}/files/{file_id}/symbols",
    response_model=List[CodeSymbolResponse],
    status_code=status.HTTP_200_OK,
    summary="List Symbols Extracted by Tree-sitter",
)
async def list_file_symbols(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> List[CodeSymbolResponse]:
    """Retrieve all functions, methods, and classes parsed via Tree-sitter for a file."""
    symbols = await ingestion_service.list_file_symbols(file_id, current_user)
    return [CodeSymbolResponse.model_validate(s) for s in symbols]
