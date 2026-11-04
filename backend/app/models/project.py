import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProjectStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    SYNCING = "syncing"
    ERROR = "error"


class Project(BaseModel):
    """Project entity representing an imported GitHub repository."""
    __tablename__ = "projects"

    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    repo_url = Column(String(512), nullable=False, index=True)
    repo_full_name = Column(String(255), nullable=False)  # e.g. "owner/repo"
    default_branch = Column(String(100), default="main", nullable=False)
    latest_commit_sha = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    is_private = Column(String(10), default="false", nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    total_files = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    total_symbols = Column(Integer, default=0, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("CodeFile", back_populates="project", cascade="all, delete-orphan")
