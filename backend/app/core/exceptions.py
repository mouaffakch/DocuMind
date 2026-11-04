from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class DocuMindException(Exception):
    """Base exception class for all DocuMind domain exceptions."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(DocuMindException):
    """Raised when a requested resource is not found."""
    pass


class AuthenticationError(DocuMindException):
    """Raised on invalid credentials or expired sessions."""
    pass


class PermissionDeniedError(DocuMindException):
    """Raised when a user attempts an unauthorized operation."""
    pass


class ConflictError(DocuMindException):
    """Raised on duplicate records (e.g. email or project already exists)."""
    pass


class IngestionError(DocuMindException):
    """Raised when repository cloning, parsing or indexing fails."""
    pass


class AIProviderError(DocuMindException):
    """Raised when the LLM or embedding service fails."""
    pass
