from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime, timezone
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.chat import router as chat_router
from app.api.v1.impact import router as impact_router
from app.api.v1.bug_analysis import router as bug_router
from app.api.v1.documentation import router as doc_router

api_router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    version: str


@api_router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Service Health Check",
)
async def health_check() -> HealthCheckResponse:
    """Returns the operational status of DocuMind API."""
    return HealthCheckResponse(
        status="operational",
        service="DocuMind Backend Core",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
    )


# Mount feature routers
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(chat_router)
api_router.include_router(impact_router)
api_router.include_router(bug_router)
api_router.include_router(doc_router)
