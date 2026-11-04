from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.chat import CitationResponse


class BugAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Bug title or brief summary")
    description: str = Field(..., min_length=10, description="Detailed problem description or GitHub issue content")
    stacktrace: Optional[str] = Field(None, description="Optional raw error stack trace or logs")


class SuspectFunction(BaseModel):
    name: str
    file_path: str
    lines: str
    suspicion_level: str  # "HIGH", "MEDIUM", "LOW"
    rationale: str


class BugAnalysisResponse(BaseModel):
    problem_summary: str
    identified_files: List[str]
    suspect_functions: List[SuspectFunction]
    hypothetical_causes: List[str]
    suggested_fixes: List[str]
    recommended_tests: List[str]
    citations: List[CitationResponse]
