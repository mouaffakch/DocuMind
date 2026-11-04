import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  GitBranch,
  Trash2,
  CheckCircle,
  ExternalLink,
  Search,
  MessageSquareCode,
  Network,
  FileCode2,
  GitPullRequest,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { projectService } from '../services/api';

export const ProjectsPage: React.FC = () => {
  const { projects, activeProject, setActiveProject, loadProjects, loadingProjects } = useProject();
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.repo_full_name && p.repo_full_name.toLowerCase().includes(search.toLowerCase())) ||
      (p.language && p.language.toLowerCase().includes(search.toLowerCase()))
  );

  const handleDelete = async (projectId: string, name: string) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer le projet "${name}" et toutes ses données vectorielles ?`)) {
      return;
    }
    setDeletingId(projectId);
    setError(null);
    try {
      await projectService.deleteProject(projectId);
      await loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression du projet.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Mes Projets Software</h1>
          <p className="text-xs text-slate-400 mt-1">
            Gérez vos dépôts synchronisés et basculez d'un projet à l'autre en un clic.
          </p>
        </div>
        <Link
          to="/import"
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-xs font-semibold text-white shadow-lg shadow-indigo-600/20 transition"
        >
          <GitPullRequest className="h-4 w-4" />
          <span>+ Importer un Dépôt</span>
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="h-4 w-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filtrer par nom ou langage..."
          className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Projects Grid */}
      {loadingProjects ? (
        <div className="flex items-center justify-center py-24 text-slate-400 space-x-3">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
          <span className="text-sm">Chargement des dépôts...</span>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-20 px-4 bg-slate-900/40 border border-slate-800 rounded-2xl">
          <FolderGit2 className="h-12 w-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">Aucun projet trouvé</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            {search ? "Aucun dépôt ne correspond à vos filtres de recherche." : "Vous n'avez pas encore importé de dépôt GitHub dans DocuMind."}
          </p>
          {!search && (
            <Link
              to="/import"
              className="inline-flex items-center space-x-2 mt-4 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg transition"
            >
              <GitPullRequest className="h-4 w-4" />
              <span>Importer un dépôt maintenant</span>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((p) => {
            const isSelected = activeProject?.id === p.id;
            return (
              <div
                key={p.id}
                className={`bg-slate-900/80 backdrop-blur border rounded-2xl p-5 flex flex-col justify-between transition group relative ${
                  isSelected
                    ? 'border-indigo-500/80 shadow-lg shadow-indigo-500/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="truncate">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-bold text-white text-base truncate">{p.name}</h3>
                        {isSelected && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold shrink-0">
                            Actif
                          </span>
                        )}
                      </div>
                      <a
                        href={p.repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-slate-400 hover:text-indigo-400 flex items-center space-x-1 mt-1 truncate"
                      >
                        <span className="truncate">{p.repo_full_name || p.repo_url}</span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 ${
                        p.status === 'READY'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : p.status === 'INDEXING'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2 py-3 border-y border-slate-800/80 text-center">
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase font-semibold">Langage</span>
                      <span className="text-xs font-medium text-slate-200">{p.language || 'Multi'}</span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase font-semibold">Fichiers</span>
                      <span className="text-xs font-mono font-medium text-slate-200">{p.total_files}</span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase font-semibold">Chunks RAG</span>
                      <span className="text-xs font-mono font-medium text-slate-200">{p.indexed_chunks}</span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center space-x-1 text-slate-500 text-xs">
                    <GitBranch className="h-3.5 w-3.5" />
                    <span>Branche : </span>
                    <span className="text-slate-300 font-mono">{p.default_branch}</span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setActiveProject(p)}
                      disabled={isSelected}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1 ${
                        isSelected
                          ? 'bg-indigo-600/20 text-indigo-300 cursor-default'
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <CheckCircle className="h-3.5 w-3.5 text-indigo-400" />
                          <span>Sélectionné</span>
                        </>
                      ) : (
                        <span>Sélectionner</span>
                      )}
                    </button>
                    <Link
                      to="/chat"
                      onClick={() => setActiveProject(p)}
                      className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600 hover:text-white text-slate-400 transition"
                      title="Ouvrir le Chat IA"
                    >
                      <MessageSquareCode className="h-4 w-4" />
                    </Link>
                    <Link
                      to="/impact"
                      onClick={() => setActiveProject(p)}
                      className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-purple-600 hover:text-white text-slate-400 transition"
                      title="Impact Analysis"
                    >
                      <Network className="h-4 w-4" />
                    </Link>
                    <Link
                      to="/explorer"
                      onClick={() => setActiveProject(p)}
                      className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-sky-600 hover:text-white text-slate-400 transition"
                      title="Exploration des fichiers"
                    >
                      <FileCode2 className="h-4 w-4" />
                    </Link>
                  </div>

                  <button
                    onClick={() => handleDelete(p.id, p.name)}
                    disabled={deletingId === p.id}
                    title="Supprimer ce projet"
                    className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition"
                  >
                    {deletingId === p.id ? (
                      <Loader2 className="h-4 w-4 animate-spin text-rose-400" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
