from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.documentation import DocumentationType


class DocumentationGenerateRequest(BaseModel):
    doc_type: DocumentationType = Field(DocumentationType.PROJECT_OVERVIEW, description="Documentation format")
    target_module: Optional[str] = Field(None, description="Specific module or file path if doc_type is MODULE")
    include_uml: bool = Field(True, description="Whether to generate Mermaid UML diagrams")


class DocumentationExportResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    doc_type: DocumentationType
    target_module: Optional[str] = None
    content_markdown: str
    mermaid_diagram: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
