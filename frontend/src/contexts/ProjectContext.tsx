import React, { createContext, useContext, useState, useEffect } from 'react';
import { Project } from '../types/api';
import { projectService } from '../services/api';
import { useAuth } from './AuthContext';

interface ProjectContextType {
  projects: Project[];
  activeProject: Project | null;
  loadingProjects: boolean;
  setActiveProject: (project: Project | null) => void;
  loadProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProjectState] = useState<Project | null>(null);
  const [loadingProjects, setLoadingProjects] = useState<boolean>(false);

  const loadProjects = async () => {
    if (!isAuthenticated) {
      setProjects([]);
      setActiveProjectState(null);
      return;
    }
    setLoadingProjects(true);
    try {
      const data = await projectService.listProjects();
      setProjects(data);

      // Restore active project or pick the first one
      const savedProjectId = localStorage.getItem('documind_active_project_id');
      const found = data.find((p) => p.id === savedProjectId);
      if (found) {
        setActiveProjectState(found);
      } else if (data.length > 0) {
        setActiveProjectState(data[0]);
        localStorage.setItem('documind_active_project_id', data[0].id);
      } else {
        setActiveProjectState(null);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoadingProjects(false);
    }
  };

  const setActiveProject = (p: Project | null) => {
    setActiveProjectState(p);
    if (p) {
      localStorage.setItem('documind_active_project_id', p.id);
    } else {
      localStorage.removeItem('documind_active_project_id');
    }
  };

  useEffect(() => {
    loadProjects();
  }, [isAuthenticated]);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        activeProject,
        loadingProjects,
        setActiveProject,
        loadProjects,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};
