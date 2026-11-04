from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query

from app.models.user import User
from app.schemas.impact import (
    ImpactAnalysisResponse,
    SymbolAutocompleteResponse,
)
from app.services.impact_service import ImpactService
from app.api.deps import get_impact_service, get_current_user

router = APIRouter(prefix="/projects/{project_id}/impact", tags=["Impact Analysis"])


@router.get(
    "",
    response_model=ImpactAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Impact Analysis for a Symbol",
)
async def analyze_impact(
    project_id: UUID,
    symbol_name: str = Query(..., min_length=1, description="Function or class name to evaluate"),
    max_depth: int = Query(3, ge=1, le=5, description="Maximum call depth to traverse"),
    current_user: User = Depends(get_current_user),
    impact_service: ImpactService = Depends(get_impact_service),
) -> ImpactAnalysisResponse:
    """
    Computes potential regression risks and dependency call graph
    for a function, class or method across the codebase.
    """
    return await impact_service.analyze_impact(project_id, symbol_name, max_depth=max_depth)


@router.get(
    "/symbols",
    response_model=List[SymbolAutocompleteResponse],
    status_code=status.HTTP_200_OK,
    summary="Search Indexed Symbols (Autocomplete)",
)
async def search_symbols(
    project_id: UUID,
    query: str = Query(..., min_length=1, description="Symbol name prefix or substring"),
    current_user: User = Depends(get_current_user),
    impact_service: ImpactService = Depends(get_impact_service),
) -> List[SymbolAutocompleteResponse]:
    """Retrieve symbols matching query to assist developers in selecting target functions."""
    return await impact_service.search_symbols(project_id, query)
