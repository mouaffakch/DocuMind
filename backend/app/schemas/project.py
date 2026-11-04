from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.project import ProjectStatus


class GitHubRepoInspectRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL or 'owner/repo' shorthand")


class GitHubRepoInfoResponse(BaseModel):
    owner: str
    repo_name: str
    full_name: str
    description: Optional[str] = None
    default_branch: str
    stars_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    is_private: bool = False
    clone_url: str
    languages: List[str] = []


class ProjectCreateRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL (e.g. https://github.com/fastapi/fastapi)")
    name: Optional[str] = Field(None, max_length=100, description="Custom project name (defaults to repository name)")
    default_branch: Optional[str] = Field(None, description="Branch to track (defaults to repo default branch)")


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    repo_url: str
    repo_full_name: str
    default_branch: str
    latest_commit_sha: Optional[str] = None
    description: Optional[str] = None
    status: ProjectStatus
    error_message: Optional[str] = None
    total_files: int
    total_chunks: int
    total_symbols: int
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSyncResponse(BaseModel):
    project_id: UUID
    status: ProjectStatus
    message: str
