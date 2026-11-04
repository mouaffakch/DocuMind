import enum
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SymbolType(str, enum.Enum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    VARIABLE = "variable"


class CodeSymbol(BaseModel):
    """Represents a syntax entity extracted via Tree-sitter AST parsing."""
    __tablename__ = "code_symbols"

    file_id = Column(Uuid(as_uuid=True), ForeignKey("code_files.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    symbol_type = Column(Enum(SymbolType), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    signature = Column(String(1024), nullable=True)
    docstring = Column(Text, nullable=True)

    # Relationships
    file = relationship("CodeFile", back_populates="symbols")
