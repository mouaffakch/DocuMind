from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.code_symbol import SymbolType


class CodeSymbolResponse(BaseModel):
    id: UUID
    name: str
    symbol_type: SymbolType
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CodeFileResponse(BaseModel):
    id: UUID
    project_id: UUID
    file_path: str
    language: str
    size_bytes: int
    sha256_hash: str
    symbols_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestionProgressResponse(BaseModel):
    project_id: UUID
    status: str
    total_files_discovered: int
    total_files_indexed: int
    total_symbols_extracted: int
    total_chunks_indexed: int
    message: str
