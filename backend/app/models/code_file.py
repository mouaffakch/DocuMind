from sqlalchemy import Column, String, Integer, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CodeFile(BaseModel):
    """Represents a code source or documentation file inside an imported project."""
    __tablename__ = "code_files"

    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1024), nullable=False, index=True)
    language = Column(String(50), nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    sha256_hash = Column(String(64), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="files")
    symbols = relationship("CodeSymbol", back_populates="file", cascade="all, delete-orphan")
