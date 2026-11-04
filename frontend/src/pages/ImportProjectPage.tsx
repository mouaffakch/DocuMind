import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  Search,
  Star,
  GitFork,
  Code2,
  GitBranch,
  ShieldAlert,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { projectService } from '../services/api';
import { RepoInspectionResult } from '../types/api';
import { useProject } from '../contexts/ProjectContext';

export const ImportProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const { loadProjects, setActiveProject } = useProject();

  const [repoUrl, setRepoUrl] = useState('');
  const [projectName, setProjectName] = useState('');
  const [inspecting, setInspecting] = useState(false);
  const [inspectionResult, setInspectionResult] = useState<RepoInspectionResult | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInspect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl) return;

    setError(null);
    setInspectionResult(null);
    setInspecting(true);

    try {
      const data = await projectService.inspectRepo(repoUrl);
      setInspectionResult(data);
      if (!projectName) {
        setProjectName(data.full_name.split('/')[1] || data.full_name);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Impossible d’inspecter ce dépôt. Vérifiez l’URL ou configurez un Personal Access Token dans les paramètres si le dépôt est privé.'
      );
    } finally {
      setInspecting(false);
    }
  };

  const handleImport = async () => {
    if (!repoUrl) return;

    setError(null);
    setImporting(true);

    try {
      const finalName = projectName || (inspectionResult ? inspectionResult.full_name.split('/')[1] : 'GitHub Repo');
      const branch = inspectionResult?.default_branch || 'main';

      const created = await projectService.createProject({
        name: finalName,
        repo_url: repoUrl,
        default_branch: branch,
      });

      setSuccess(`Projet "${created.name}" importé avec succès ! Indexation AST & vectorielle enclenchée.`);
      await loadProjects();
      setActiveProject(created);

      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l’importation du projet.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-white">Importer un Dépôt GitHub</h1>
        <p className="text-xs text-slate-400 mt-1">
          DocuMind va inspecter la structure du dépôt, filtrer les fichiers sensibles, parser l’AST Tree-sitter et indexer les vecteurs.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-start space-x-3 text-emerald-300 text-sm">
          <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {/* Step 1: Input URL and Inspect */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div>
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <span className="flex items-center justify-center h-6 w-6 rounded-full bg-indigo-600 text-white text-xs">
              1
            </span>
            <span>Renseignez l'URL du dépôt GitHub</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Prend en charge les dépôts publics et privés (authentifiés via votre PAT GitHub).
          </p>
        </div>

        <form onSubmit={handleInspect} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <GitPullRequest className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="url"
              required
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/organization/repository"
              className="block w-full pl-10 pr-3 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={inspecting || !repoUrl}
            className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition disabled:opacity-50 shrink-0"
          >
            {inspecting ? (
              <>
                <Loader2 className="animate-spin h-4 w-4 text-indigo-400" />
                <span>Inspection GitHub...</span>
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                <span>Inspecter le dépôt</span>
              </>
            )}
          </button>
        </form>

        {/* Inspection Result Preview */}
        {inspectionResult && (
          <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4 animate-in fade-in duration-300">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-white text-sm">{inspectionResult.full_name}</h3>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      inspectionResult.is_private
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    {inspectionResult.is_private ? 'Privé' : 'Public'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 max-w-xl">
                  {inspectionResult.description || 'Aucune description disponible pour ce dépôt.'}
                </p>
              </div>

              <a
                href={inspectionResult.clone_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
              >
                <span>Voir sur GitHub</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800/80 text-xs">
              <div className="flex items-center space-x-2 text-slate-300">
                <Star className="h-4 w-4 text-amber-400" />
                <span>{inspectionResult.stars} étoiles</span>
              </div>
              <div className="flex items-center space-x-2 text-slate-300">
                <GitFork className="h-4 w-4 text-purple-400" />
                <span>{inspectionResult.forks} forks</span>
              </div>
              <div className="flex items-center space-x-2 text-slate-300">
                <Code2 className="h-4 w-4 text-indigo-400" />
                <span>{inspectionResult.language || 'Non spécifié'}</span>
              </div>
              <div className="flex items-center space-x-2 text-slate-300">
                <GitBranch className="h-4 w-4 text-sky-400" />
                <span className="font-mono">{inspectionResult.default_branch}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Step 2: Finalize and Confirm Import */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div>
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <span className="flex items-center justify-center h-6 w-6 rounded-full bg-indigo-600 text-white text-xs">
              2
            </span>
            <span>Configuration et Déclenchement de l'Indexation</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Définissez un alias convivial pour retrouver votre projet dans le dashboard.
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Nom du Projet dans DocuMind
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="ex: Mon-Projet-Microservices"
              className="block w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
            <ShieldAlert className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-200">Garanties de Sécurité DocuMind :</p>
              <ul className="list-disc list-inside mt-1 space-y-0.5 text-[11px]">
                <li>Les fichiers <code className="text-slate-300">.env</code>, clés RSA et secrets sont strictement ignorés.</li>
                <li>Le code source n'est jamais exécuté dynamiquement sur nos serveurs.</li>
                <li>Seuls l'analyse syntaxique (Tree-sitter) et les embeddings sémantiques sont générés.</li>
              </ul>
            </div>
          </div>

          <button
            onClick={handleImport}
            disabled={importing || !repoUrl}
            className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-xs font-bold text-white shadow-lg shadow-indigo-600/25 transition disabled:opacity-50"
          >
            {importing ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                <span>Importation et indexation en cours...</span>
              </>
            ) : (
              <>
                <span>Créer et Indexer le Projet</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
