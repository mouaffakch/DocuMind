from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class GraphNode(BaseModel):
    id: str
    label: str
    symbol_name: str
    file_path: str
    line: int
    node_type: str  # "target", "caller", "test"


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str  # "calls", "imports", "inherits"


class RiskAssessment(BaseModel):
    level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    score: float  # 0.0 to 1.0
    direct_callers_count: int
    transitive_callers_count: int
    affected_files_count: int
    affected_tests_count: int
    explanation: str


class ImpactAnalysisResponse(BaseModel):
    target_symbol: str
    target_file: Optional[str] = None
    target_line: Optional[int] = None
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    impacted_files: List[str]
    affected_tests: List[str]
    risk_assessment: RiskAssessment

    model_config = ConfigDict(from_attributes=True)


class SymbolAutocompleteResponse(BaseModel):
    id: UUID
    name: str
    symbol_type: str
    file_path: str
    start_line: int
    signature: Optional[str] = None
