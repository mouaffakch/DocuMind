import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  HealthCheckResponse,
  User,
  TokenResponse,
  Project,
  RepoInspectionResult,
  CodeFile,
  ChatSession,
  ChatMessage,
  ImpactAnalysisResponse,
  BugAnalysisResponse,
  DocumentationResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Attach JWT access token to outbound requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('documind_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor: automatically remove token on 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('documind_access_token');
    }
    return Promise.reject(error);
  }
);

// System API
export const systemService = {
  checkHealth: async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },
};

// Auth API
export const authService = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    localStorage.setItem('documind_access_token', response.data.access_token);
    return response.data;
  },
  register: async (email: string, password: string, fullName: string): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
  setGitHubPAT: async (token: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/github-token', { token });
    return response.data;
  },
  deleteGitHubPAT: async (): Promise<void> => {
    await apiClient.delete('/auth/github-token');
  },
  logout: () => {
    localStorage.removeItem('documind_access_token');
  },
};

// Project API
export const projectService = {
  listProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },
  getProject: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },
  inspectRepo: async (repoUrl: string): Promise<RepoInspectionResult> => {
    const response = await apiClient.post<RepoInspectionResult>('/projects/inspect', {
      repo_url: repoUrl,
    });
    return response.data;
  },
  createProject: async (data: { name: string; repo_url: string; default_branch?: string }): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },
  deleteProject: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/projects/${projectId}`);
  },
  listFiles: async (projectId: string): Promise<CodeFile[]> => {
    const response = await apiClient.get<CodeFile[]>(`/projects/${projectId}/files`);
    return response.data;
  },
};

// Chat API
export const chatService = {
  listSessions: async (projectId: string): Promise<ChatSession[]> => {
    const response = await apiClient.get<ChatSession[]>(`/projects/${projectId}/chat/sessions`);
    return response.data;
  },
  createSession: async (projectId: string, title?: string): Promise<ChatSession> => {
    const response = await apiClient.post<ChatSession>(`/projects/${projectId}/chat/sessions`, {
      title: title || 'Nouvelle discussion',
    });
    return response.data;
  },
  getSession: async (projectId: string, sessionId: string): Promise<ChatSession> => {
    const response = await apiClient.get<ChatSession>(`/projects/${projectId}/chat/sessions/${sessionId}`);
    return response.data;
  },
  sendMessage: async (
    projectId: string,
    sessionId: string,
    message: string
  ): Promise<ChatMessage> => {
    const response = await apiClient.post<ChatMessage>(
      `/projects/${projectId}/chat/sessions/${sessionId}/messages`,
      { message }
    );
    return response.data;
  },
};

// Impact Analysis API
export const impactService = {
  analyze: async (projectId: string, symbolName: string, maxDepth: number = 3): Promise<ImpactAnalysisResponse> => {
    const response = await apiClient.get<ImpactAnalysisResponse>(
      `/projects/${projectId}/impact?symbol_name=${encodeURIComponent(symbolName)}&max_depth=${maxDepth}`
    );
    return response.data;
  },
  autocompleteSymbols: async (
    projectId: string,
    query: string
  ): Promise<Array<{ name: string; file_path: string; symbol_type: string; line: number }>> => {
    const response = await apiClient.get<Array<{ name: string; file_path: string; symbol_type: string; line: number }>>(
      `/projects/${projectId}/impact/symbols?query=${encodeURIComponent(query)}`
    );
    return response.data;
  },
};

// Bug Analysis API
export const bugAnalysisService = {
  analyze: async (
    projectId: string,
    data: { title: string; description: string; stacktrace?: string }
  ): Promise<BugAnalysisResponse> => {
    const response = await apiClient.post<BugAnalysisResponse>(
      `/projects/${projectId}/bug-analysis`,
      data
    );
    return response.data;
  },
};

// Documentation & UML API
export const docService = {
  generateProjectDoc: async (projectId: string): Promise<DocumentationResponse> => {
    const response = await apiClient.post<DocumentationResponse>(
      `/projects/${projectId}/docs/overview`
    );
    return response.data;
  },
  generateModuleDoc: async (projectId: string, modulePath: string): Promise<DocumentationResponse> => {
    const response = await apiClient.post<DocumentationResponse>(
      `/projects/${projectId}/docs/module?module_path=${encodeURIComponent(modulePath)}`
    );
    return response.data;
  },
  generateUMLDiagram: async (projectId: string): Promise<DocumentationResponse> => {
    const response = await apiClient.post<DocumentationResponse>(
      `/projects/${projectId}/docs/uml`
    );
    return response.data;
  },
};
