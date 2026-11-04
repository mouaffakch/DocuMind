from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project, ProjectStatus
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository handling database operations for Project entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def list_by_owner(self, owner_id: UUID) -> List[Project]:
        """Fetch all projects owned by a specific user, ordered by creation date desc."""
        stmt = select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_owner_and_id(self, owner_id: UUID, project_id: UUID) -> Optional[Project]:
        """Find a project owned by a specific user."""
        stmt = select(Project).where(Project.owner_id == owner_id, Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_repo_and_owner(self, owner_id: UUID, repo_full_name: str) -> Optional[Project]:
        """Find if a repository has already been imported by this user."""
        stmt = select(Project).where(
            Project.owner_id == owner_id,
            Project.repo_full_name.ilike(repo_full_name.strip())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
