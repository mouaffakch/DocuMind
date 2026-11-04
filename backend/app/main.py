from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.exceptions import (
    DocuMindException,
    EntityNotFoundError,
    AuthenticationError,
    PermissionDeniedError,
    ConflictError,
)
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("documind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} API in {settings.ENVIRONMENT} mode...")
    try:
        from app.core.database import async_engine, Base
        import app.models.user
        import app.models.project
        import app.models.code_file
        import app.models.code_symbol
        import app.models.chat
        import app.models.dependency
        import app.models.documentation
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified and synchronized.")
    except Exception as e:
        logger.warning(f"Could not automatically synchronize database schema on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} API...")


def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    application = FastAPI(
        title=f"{settings.PROJECT_NAME} API",
        description="AI-Powered Software Documentation & Code Intelligence Assistant Backend.",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    @application.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "message": exc.message, "details": exc.details},
        )

    @application.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized", "message": exc.message, "details": exc.details},
        )

    @application.exception_handler(PermissionDeniedError)
    async def permission_error_handler(request: Request, exc: PermissionDeniedError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Forbidden", "message": exc.message, "details": exc.details},
        )

    @application.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Conflict", "message": exc.message, "details": exc.details},
        )

    @application.exception_handler(DocuMindException)
    async def general_documind_handler(request: Request, exc: DocuMindException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Bad Request", "message": exc.message, "details": exc.details},
        )

    # Mount API routers
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_application()
