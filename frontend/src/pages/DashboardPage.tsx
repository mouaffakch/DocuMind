import React from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  FileCode2,
  Database,
  Activity,
  ArrowUpRight,
  GitPullRequest,
  MessageSquareCode,
  Network,
  Bug,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { useAuth } from '../contexts/AuthContext';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { projects, activeProject, setActiveProject, loadProjects, loadingProjects } = useProject();

  const totalFiles = projects.reduce((acc, p) => acc + (p.total_files || 0), 0);
  const totalChunks = projects.reduce((acc, p) => acc + (p.indexed_chunks || 0), 0);
  const readyProjects = projects.filter((p) => p.status === 'READY').length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              DocuMind Code Intelligence
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            Bienvenue, {user?.full_name || 'Développeur'} !
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Explorez, interrogez et documentez vos projets logiciels grâce au RAG conscient de l'AST.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => loadProjects()}
            disabled={loadingProjects}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            <RotateCw className={`h-3.5 w-3.5 ${loadingProjects ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          <Link
            to="/import"
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-xs font-semibold text-white shadow-lg shadow-indigo-600/20 transition"
          >
            <GitPullRequest className="h-3.5 w-3.5" />
            <span>+ Importer un Dépôt</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1 */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-800 p-5 rounded-2xl relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Projets Déposés</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <FolderGit2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{projects.length}</span>
            <span className="text-xs text-emerald-400 font-medium">{readyProjects} prêts</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Dépôts GitHub indexés dans le cluster</p>
        </div>

        {/* Metric 2 */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-800 p-5 rounded-2xl relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Fichiers Analysés</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <FileCode2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{totalFiles}</span>
            <span className="text-xs text-purple-400 font-medium">AST Tree-sitter</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Fichiers source sans secrets ni binaires</p>
        </div>

        {/* Metric 3 */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-800 p-5 rounded-2xl relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Chunks Indexés</span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <Database className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{totalChunks}</span>
            <span className="text-xs text-sky-400 font-medium">Vecteurs Qdrant</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Recherche hybride dense + BM25</p>
        </div>

        {/* Metric 4 */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-800 p-5 rounded-2xl relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">État du Moteur RAG</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Activity className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold text-emerald-400 flex items-center space-x-1.5">
              <CheckCircle2 className="h-5 w-5" />
              <span>Opérationnel</span>
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Reranker & LLM synchronisés</p>
        </div>
      </div>

      {/* Quick Action Shortcuts */}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
          Actions Rapides
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/chat"
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/60 transition group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition">
                <MessageSquareCode className="h-5 w-5" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-indigo-400 transition" />
            </div>
            <div className="mt-4">
              <h3 className="font-semibold text-slate-200 text-sm group-hover:text-white">Interroger le Code</h3>
              <p className="text-xs text-slate-400 mt-1">Posez une question en langage naturel avec citations exactes.</p>
            </div>
          </Link>

          <Link
            to="/impact"
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/50 hover:bg-slate-800/60 transition group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500 group-hover:text-white transition">
                <Network className="h-5 w-5" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-purple-400 transition" />
            </div>
            <div className="mt-4">
              <h3 className="font-semibold text-slate-200 text-sm group-hover:text-white">Impact Analysis</h3>
              <p className="text-xs text-slate-400 mt-1">Visualisez les dépendances et prévenez les régressions.</p>
            </div>
          </Link>

          <Link
            to="/bugs"
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-rose-500/50 hover:bg-slate-800/60 transition group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 group-hover:bg-rose-500 group-hover:text-white transition">
                <Bug className="h-5 w-5" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-rose-400 transition" />
            </div>
            <div className="mt-4">
              <h3 className="font-semibold text-slate-200 text-sm group-hover:text-white">Analyse des Bugs</h3>
              <p className="text-xs text-slate-400 mt-1">Triez un bug ou une stacktrace et isolez les suspects.</p>
            </div>
          </Link>

          <Link
            to="/docs"
            className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/60 transition group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 group-hover:bg-sky-500 group-hover:text-white transition">
                <Sparkles className="h-5 w-5" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-slate-500 group-hover:text-sky-400 transition" />
            </div>
            <div className="mt-4">
              <h3 className="font-semibold text-slate-200 text-sm group-hover:text-white">Générer la Doc & UML</h3>
              <p className="text-xs text-slate-400 mt-1">Générez un diagramme de classes Mermaid et l'architecture.</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Projects Table & Active Project Focus */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Projects List */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Dépôts Récents</h2>
              <p className="text-xs text-slate-400">Sélectionnez un projet pour basculer le contexte de travail</p>
            </div>
            <Link
              to="/projects"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
            >
              <span>Voir tout</span>
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-12 px-4 border border-dashed border-slate-800 rounded-xl">
              <FolderGit2 className="h-10 w-10 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-300 font-medium">Aucun projet importé pour le moment</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Commencez par importer un dépôt GitHub public ou privé pour initialiser l'indexation.
              </p>
              <Link
                to="/import"
                className="inline-flex items-center space-x-1.5 mt-4 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg transition"
              >
                <GitPullRequest className="h-3.5 w-3.5" />
                <span>Importer mon premier dépôt</span>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="pb-3">Nom du Dépôt</th>
                    <th className="pb-3">Statut</th>
                    <th className="pb-3">Langage</th>
                    <th className="pb-3 text-right">Fichiers</th>
                    <th className="pb-3 text-right">Chunks</th>
                    <th className="pb-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {projects.slice(0, 5).map((proj) => {
                    const isSelected = activeProject?.id === proj.id;
                    return (
                      <tr
                        key={proj.id}
                        className={`hover:bg-slate-800/40 transition ${
                          isSelected ? 'bg-indigo-950/20' : ''
                        }`}
                      >
                        <td className="py-3 font-medium text-slate-200">
                          <div className="flex items-center space-x-2">
                            <span>{proj.name}</span>
                            {isSelected && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                Actif
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono block truncate max-w-xs">
                            {proj.repo_full_name || proj.repo_url}
                          </span>
                        </td>
                        <td className="py-3">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              proj.status === 'READY'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : proj.status === 'INDEXING'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {proj.status}
                          </span>
                        </td>
                        <td className="py-3 text-slate-400">{proj.language || 'Multi'}</td>
                        <td className="py-3 text-right font-mono text-slate-300">{proj.total_files}</td>
                        <td className="py-3 text-right font-mono text-slate-300">{proj.indexed_chunks}</td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => setActiveProject(proj)}
                            disabled={isSelected}
                            className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                              isSelected
                                ? 'text-slate-500 cursor-default'
                                : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                            }`}
                          >
                            {isSelected ? 'Sélectionné' : 'Activer'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Active Project Card / Summary */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                Focus Projet Actif
              </span>
              {activeProject && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Synchronisé
                </span>
              )}
            </div>

            {activeProject ? (
              <div className="mt-4 space-y-4">
                <div>
                  <h3 className="text-lg font-bold text-white">{activeProject.name}</h3>
                  <a
                    href={activeProject.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-400 hover:underline flex items-center space-x-1 mt-0.5"
                  >
                    <span className="truncate">{activeProject.repo_url}</span>
                    <ArrowUpRight className="h-3 w-3 shrink-0" />
                  </a>
                </div>

                <div className="space-y-2 border-t border-b border-slate-800 py-3 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Branche par défaut :</span>
                    <span className="text-slate-200 font-mono">{activeProject.default_branch}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Fichiers scannés :</span>
                    <span className="text-slate-200 font-mono">{activeProject.total_files}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Vecteurs indexés :</span>
                    <span className="text-slate-200 font-mono">{activeProject.indexed_chunks}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Créé le :</span>
                    <span className="text-slate-200">
                      {new Date(activeProject.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 pt-1">
                  <Link
                    to="/chat"
                    className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition shadow-sm"
                  >
                    <MessageSquareCode className="h-4 w-4" />
                    <span>Lancer une discussion RAG</span>
                  </Link>
                  <Link
                    to="/impact"
                    className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
                  >
                    <Network className="h-4 w-4" />
                    <span>Explorer le graphe d'impact</span>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="mt-8 text-center text-slate-400 text-xs py-8">
                <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto mb-2" />
                <p>Aucun projet actif sélectionné.</p>
                <p className="text-slate-500 mt-1">Sélectionnez-en un dans la liste ou importez-en un nouveau.</p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span className="flex items-center space-x-1">
              <Clock className="h-3.5 w-3.5" />
              <span>Dernière synchro : Récent</span>
            </span>
            <span className="text-indigo-400 font-medium">v1.0.0</span>
          </div>
        </div>
      </div>
    </div>
  );
};
