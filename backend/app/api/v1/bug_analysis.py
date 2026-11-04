from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.models.user import User
from app.schemas.bug_analysis import (
    BugAnalysisRequest,
    BugAnalysisResponse,
)
from app.services.bug_analysis_service import BugAnalysisService
from app.api.deps import get_bug_analysis_service, get_current_user

router = APIRouter(prefix="/projects/{project_id}/bug-analysis", tags=["Bug Analysis & Triage"])


@router.post(
    "",
    response_model=BugAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Bug or GitHub Issue",
)
async def analyze_bug(
    project_id: UUID,
    data: BugAnalysisRequest,
    current_user: User = Depends(get_current_user),
    bug_service: BugAnalysisService = Depends(get_bug_analysis_service),
) -> BugAnalysisResponse:
    """
    Investigates a bug description, stack trace, or GitHub issue.
    Identifies suspect functions and files with citations, without dogmatic assumptions.
    """
    return await bug_service.analyze_bug(project_id, data)
