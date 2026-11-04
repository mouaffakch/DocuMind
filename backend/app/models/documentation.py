import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DocumentationType(str, enum.Enum):
    MODULE = "module"
    PROJECT_OVERVIEW = "project_overview"
    UML_DIAGRAM = "uml_diagram"
    API_REFERENCE = "api_reference"


class DocumentationExport(BaseModel):
    """Represents a generated technical document or UML diagram for a project."""
    __tablename__ = "documentation_exports"

    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(Enum(DocumentationType), default=DocumentationType.PROJECT_OVERVIEW, nullable=False)
    target_module = Column(String(512), nullable=True)
    content_markdown = Column(Text, nullable=False)
    mermaid_diagram = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project")
    user = relationship("User")
