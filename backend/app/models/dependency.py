import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DependencyType(str, enum.Enum):
    CALL = "call"
    IMPORT = "import"
    INHERITANCE = "inheritance"


class SymbolDependency(BaseModel):
    """Represents a static dependency relationship (call, import, inheritance) between code entities."""
    __tablename__ = "symbol_dependencies"

    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    caller_name = Column(String(255), nullable=False, index=True)
    caller_file_path = Column(String(1024), nullable=False)
    caller_line = Column(Integer, nullable=False)
    callee_name = Column(String(255), nullable=False, index=True)
    dependency_type = Column(Enum(DependencyType), default=DependencyType.CALL, nullable=False)

    # Relationships
    project = relationship("Project")
