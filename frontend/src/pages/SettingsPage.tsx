import React, { useState } from 'react';
import {
  User as UserIcon,
  Key,
  Shield,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/api';

export const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [githubToken, setGithubToken] = useState('');
  const [savingToken, setSavingToken] = useState(false);
  const [deletingToken, setDeletingToken] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSaveToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubToken.trim()) return;

    setSavingToken(true);
    setError(null);
    setSuccess(null);

    try {
      await authService.setGitHubPAT(githubToken.trim());
      setSuccess('Personal Access Token GitHub chiffré et sauvegardé avec succès.');
      setGithubToken('');
      await refreshUser();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l’enregistrement du token GitHub.');
    } finally {
      setSavingToken(false);
    }
  };

  const handleDeleteToken = async () => {
    if (!window.confirm('Voulez-vous révoquer l’accès GitHub enregistré pour ce compte ?')) {
      return;
    }
    setDeletingToken(true);
    setError(null);
    setSuccess(null);

    try {
      await authService.deleteGitHubPAT();
      setSuccess('Jeton GitHub révoqué.');
      await refreshUser();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression du jeton.');
    } finally {
      setDeletingToken(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-white">Paramètres & Sécurité du Compte</h1>
        <p className="text-xs text-slate-400 mt-1">
          Gérez votre profil utilisateur et vos identifiants d'accès GitHub sécurisés par chiffrement symétrique Fernet.
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

      {/* Profile Details Card */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center space-x-2">
          <UserIcon className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-white">Profil Développeur</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="block text-[10px] uppercase font-semibold text-slate-500">Nom Complet</span>
            <span className="text-xs font-semibold text-slate-200 mt-0.5 block">{user?.full_name}</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="block text-[10px] uppercase font-semibold text-slate-500">Email</span>
            <span className="text-xs font-mono text-slate-200 mt-0.5 block">{user?.email}</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="block text-[10px] uppercase font-semibold text-slate-500">Rôle / Privilèges</span>
            <span className="text-xs font-mono font-bold text-indigo-400 mt-0.5 block">{user?.role}</span>
          </div>
        </div>
      </div>

      {/* GitHub Personal Access Token Management */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Key className="h-5 w-5 text-purple-400" />
            <h2 className="text-base font-bold text-white">Intégration GitHub (PAT)</h2>
          </div>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
              user?.has_github_token
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-slate-800 text-slate-400'
            }`}
          >
            {user?.has_github_token ? 'Jeton actif configuré' : 'Aucun jeton'}
          </span>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Un Personal Access Token (PAT) GitHub est requis pour importer vos dépôts privés ou augmenter la limite de requêtes API (rate limiting). DocuMind chiffre ce jeton au repos via Fernet.
        </p>

        {user?.has_github_token && (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <span className="text-xs text-slate-300 font-mono">ghp_••••••••••••••••••••••••••••••••</span>
            </div>
            <button
              onClick={handleDeleteToken}
              disabled={deletingToken}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs transition border border-rose-500/20"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Révoquer</span>
            </button>
          </div>
        )}

        <form onSubmit={handleSaveToken} className="space-y-3 pt-2">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
            {user?.has_github_token ? 'Mettre à jour le Personal Access Token' : 'Ajouter un nouveau Personal Access Token'}
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="password"
              required
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              className="flex-1 px-3.5 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={savingToken || !githubToken.trim()}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition shadow-sm disabled:opacity-50 flex items-center justify-center space-x-1.5 shrink-0"
            >
              {savingToken ? (
                <>
                  <Loader2 className="animate-spin h-3.5 w-3.5" />
                  <span>Chiffrement...</span>
                </>
              ) : (
                <span>Enregistrer</span>
              )}
            </button>
          </div>
          <a
            href="https://github.com/settings/tokens/new?scopes=repo,read:org"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center space-x-1 pt-1"
          >
            <span>Créer un token sur GitHub avec les permissions "repo"</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </form>
      </div>
    </div>
  );
};
