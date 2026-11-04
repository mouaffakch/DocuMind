from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.repositories.project_repository import ProjectRepository
from app.services.github_service import GitHubService
from app.schemas.project import ProjectCreateRequest, ProjectSyncResponse
from app.core.exceptions import (
    EntityNotFoundError,
    ConflictError,
    DocuMindException,
)


class ProjectService:
    """Service handling repository imports, listing, deletion, and sync triggers."""

    def __init__(self, session: AsyncSession, auth_service=None):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.auth_service = auth_service

    async def create_project(self, user: User, data: ProjectCreateRequest) -> Project:
        """Import a repository and register the project for the user."""
        owner, repo_name = GitHubService.parse_repo_url(data.repo_url)
        repo_full_name = f"{owner}/{repo_name}"

        # Check duplicate import by this user
        existing = await self.project_repo.get_by_repo_and_owner(user.id, repo_full_name)
        if existing:
            raise ConflictError(f"Le dépôt '{repo_full_name}' a déjà été importé dans vos projets.")

        # Get user's decrypted PAT if available
        pat = None
        if self.auth_service:
            pat = self.auth_service.get_decrypted_pat(user)

        # Inspect repository via GitHub API to validate access & get metadata
        repo_info = await GitHubService.get_repo_metadata(owner, repo_name, pat=pat)

        # Determine branch and commit SHA
        target_branch = data.default_branch or repo_info.default_branch
        latest_commit = await GitHubService.get_latest_commit_sha(owner, repo_name, branch=target_branch, pat=pat)

        project_name = data.name.strip() if data.name else repo_info.repo_name

        project = Project(
            owner_id=user.id,
            name=project_name,
            repo_url=data.repo_url.strip(),
            repo_full_name=repo_full_name,
            default_branch=target_branch,
            latest_commit_sha=latest_commit,
            description=repo_info.description,
            is_private="true" if repo_info.is_private else "false",
            status=ProjectStatus.PENDING,
            total_files=0,
            total_chunks=0,
            total_symbols=0,
        )

        created_project = await self.project_repo.create(project)
        return created_project

    async def list_user_projects(self, user: User) -> List[Project]:
        """List all projects belonging to the user."""
        return await self.project_repo.list_by_owner(user.id)

    async def get_project(self, user: User, project_id: UUID) -> Project:
        """Get a project by ID, ensuring user ownership."""
        project = await self.project_repo.get_by_owner_and_id(user.id, project_id)
        if not project:
            raise EntityNotFoundError(f"Projet introuvable avec l'identifiant '{project_id}'.")
        return project

    async def delete_project(self, user: User, project_id: UUID) -> None:
        """Delete a project and its cascaded data."""
        project = await self.get_project(user, project_id)
        await self.project_repo.delete(project)

    async def trigger_sync(self, user: User, project_id: UUID) -> ProjectSyncResponse:
        """Trigger project synchronization with the remote repository."""
        project = await self.get_project(user, project_id)

        pat = None
        if self.auth_service:
            pat = self.auth_service.get_decrypted_pat(user)

        owner, repo_name = GitHubService.parse_repo_url(project.repo_url)
        latest_commit = await GitHubService.get_latest_commit_sha(
            owner, repo_name, branch=project.default_branch, pat=pat
        )

        project.latest_commit_sha = latest_commit
        project.status = ProjectStatus.SYNCING
        project.last_synced_at = datetime.now(timezone.utc)
        await self.project_repo.update(project)

        return ProjectSyncResponse(
            project_id=project.id,
            status=project.status,
            message=f"Synchronisation démarrée pour '{project.name}' (Commit: {latest_commit[:7] if latest_commit else 'N/A'}).",
        )
