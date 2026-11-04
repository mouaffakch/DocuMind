from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models.user import User
from app.schemas.documentation import (
    DocumentationGenerateRequest,
    DocumentationExportResponse,
)
from app.services.doc_service import DocService
from app.api.deps import get_doc_service, get_current_user

router = APIRouter(prefix="/projects/{project_id}/documentation", tags=["Automated Documentation & UML"])


@router.post(
    "/generate",
    response_model=DocumentationExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Technical Documentation or UML Diagram",
)
async def generate_documentation(
    project_id: UUID,
    data: DocumentationGenerateRequest,
    current_user: User = Depends(get_current_user),
    doc_service: DocService = Depends(get_doc_service),
) -> DocumentationExportResponse:
    """Generate structured markdown documentation, module summaries or Mermaid class diagrams."""
    return await doc_service.generate_documentation(current_user, project_id, data)


@router.get(
    "",
    response_model=List[DocumentationExportResponse],
    status_code=status.HTTP_200_OK,
    summary="List Generated Documents",
)
async def list_documentation(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    doc_service: DocService = Depends(get_doc_service),
) -> List[DocumentationExportResponse]:
    """Retrieve history of all generated documentation files for this project."""
    return await doc_service.list_exports(current_user, project_id)


@router.get(
    "/{export_id}",
    response_model=DocumentationExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Document",
)
async def get_documentation(
    project_id: UUID,
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    doc_service: DocService = Depends(get_doc_service),
) -> DocumentationExportResponse:
    """Get full markdown content and Mermaid diagram for an exported document."""
    return await doc_service.get_export(current_user, export_id)


@router.delete(
    "/{export_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Generated Document",
)
async def delete_documentation(
    project_id: UUID,
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    doc_service: DocService = Depends(get_doc_service),
) -> None:
    """Delete a documentation record."""
    await doc_service.delete_export(current_user, export_id)
