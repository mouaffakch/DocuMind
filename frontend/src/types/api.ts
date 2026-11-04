export interface HealthCheckResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// User & Auth
export type UserRole = 'ADMIN' | 'DEVELOPER' | 'VIEWER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  has_github_token: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Project
export type ProjectStatus = 'PENDING' | 'CLONING' | 'INDEXING' | 'READY' | 'ERROR';

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  repo_url: string;
  repo_full_name?: string;
  default_branch: string;
  status: ProjectStatus;
  language?: string;
  total_files: number;
  indexed_chunks: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface RepoInspectionResult {
  full_name: string;
  description: string;
  stars: number;
  forks: number;
  open_issues: number;
  default_branch: string;
  language: string;
  license?: string;
  is_private: boolean;
  clone_url: string;
}

// Code & AST Symbols
export interface CodeSymbol {
  id: string;
  name: string;
  symbol_type: string;
  start_line: number;
  end_line: number;
  signature?: string;
  docstring?: string;
}

export interface CodeFile {
  id: string;
  file_path: string;
  language: string;
  size_bytes: number;
  symbols?: CodeSymbol[];
}

// Chat & Citations
export interface Citation {
  id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  relevance_score: number;
  code_snippet: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  citations?: Citation[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  messages?: ChatMessage[];
}

// Impact Analysis
export interface ImpactNode {
  id: string;
  label: string;
  file_path: string;
  node_type: string;
  depth: number;
  is_test: boolean;
}

export interface ImpactEdge {
  source: string;
  target: string;
  label: string;
}

export interface RiskAssessment {
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score: number;
  direct_callers_count: number;
  transitive_callers_count: number;
  affected_tests_count: number;
  explanation: string;
}

export interface ImpactAnalysisResponse {
  target_symbol: string;
  target_file: string;
  target_line: number;
  max_depth: number;
  nodes: ImpactNode[];
  edges: ImpactEdge[];
  affected_tests: string[];
  impacted_files: string[];
  risk_assessment: RiskAssessment;
}

// Bug Analysis
export interface SuspectFunction {
  name: string;
  file_path: string;
  lines: string;
  suspicion_level: 'HIGH' | 'MEDIUM' | 'LOW';
  rationale: string;
}

export interface BugAnalysisResponse {
  problem_summary: string;
  identified_files: string[];
  suspect_functions: SuspectFunction[];
  hypothetical_causes: string[];
  suggested_fixes: string[];
  recommended_tests: string[];
  citations: Citation[];
}

// Documentation
export interface DocumentationResponse {
  project_id: string;
  title: string;
  doc_type: 'PROJECT_OVERVIEW' | 'MODULE_GUIDE' | 'UML_CLASS_DIAGRAM';
  markdown_content: string;
  uml_diagram?: string;
  file_path?: string;
}
