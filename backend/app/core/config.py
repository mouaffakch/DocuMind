from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    PROJECT_NAME: str = "DocuMind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Security
    SECRET_KEY: str = "documind-super-secret-dev-key-change-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: Optional[str] = None  # Base64 Fernet key for external PATs

    # PostgreSQL Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "documind_user"
    POSTGRES_PASSWORD: str = "documind_password"
    POSTGRES_DB: str = "documind_db"
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_async_db_url(cls, v: Optional[str], info) -> str:
        if v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('POSTGRES_USER', 'documind_user')}:"
            f"{data.get('POSTGRES_PASSWORD', 'documind_password')}@"
            f"{data.get('POSTGRES_SERVER', 'localhost')}:{data.get('POSTGRES_PORT', 5432)}/"
            f"{data.get('POSTGRES_DB', 'documind_db')}"
        )

    @field_validator("SYNC_DATABASE_URL", mode="before")
    def assemble_sync_db_url(cls, v: Optional[str], info) -> str:
        if v:
            return v
        data = info.data
        return (
            f"postgresql://{data.get('POSTGRES_USER', 'documind_user')}:"
            f"{data.get('POSTGRES_PASSWORD', 'documind_password')}@"
            f"{data.get('POSTGRES_SERVER', 'localhost')}:{data.get('POSTGRES_PORT', 5432)}/"
            f"{data.get('POSTGRES_DB', 'documind_db')}"
        )

    # Qdrant Vector Store
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION_NAME: str = "documind_code_chunks"

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Temporary storage path for git clones
    CLONE_DIR: str = "./cloned_repos"


settings = Settings()
