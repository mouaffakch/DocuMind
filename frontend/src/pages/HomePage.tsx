import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bot, 
  GitBranch, 
  Code2, 
  ShieldCheck, 
  Zap, 
  Terminal, 
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  LogIn,
  UserPlus
} from 'lucide-react';
import { systemService } from '../services/api';
import { HealthCheckResponse } from '../types/api';

export const HomePage: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const data = await systemService.checkHealth();
        setHealth(data);
        setError(null);
      } catch (err: unknown) {
        setError('Impossible de joindre le backend FastAPI. Vérifiez que le serveur est démarré.');
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Bot className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-emerald-400 bg-clip-text text-transparent">
                DocuMind
              </span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                v1.0.0
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="text-slate-400 hidden sm:inline">Statut Backend:</span>
              {loading ? (
                <span className="text-yellow-400">Connexion...</span>
              ) : health ? (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Opérationnel
                </span>
              ) : (
                <span className="text-rose-400 font-medium flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> Hors-ligne
                </span>
              )}
            </div>

            <Link
              to="/login"
              className="text-xs font-semibold text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-800 transition flex items-center gap-1.5"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Connexion</span>
            </Link>

            <Link
              to="/register"
              className="text-xs font-semibold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-300 hover:from-emerald-300 hover:to-teal-200 px-3.5 py-1.5 rounded-lg shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Inscription</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-sm font-medium">
            <Zap className="w-4 h-4" /> AI-Powered Software Documentation & Code Intelligence
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl text-white">
            Comprenez, explorez et interrogez vos dépôts en{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              langage naturel
            </span>
          </h1>
          <p className="text-lg text-slate-400">
            DocuMind combine l'analyse syntaxique formelle (Tree-sitter AST) et le RAG Hybride pour transformer vos projets GitHub en une base de connaissances vérifiable avec citations exactes.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/register"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/25 transition flex items-center justify-center gap-2"
            >
              <span>Créer un compte & Explorer</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/login"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold text-sm transition flex items-center justify-center gap-2"
            >
              <LogIn className="w-4 h-4 text-emerald-400" />
              <span>Se Connecter</span>
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-emerald-500/30 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
              <Code2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">AST-Aware RAG</h3>
            <p className="text-sm text-slate-400">
              Découpage sémantique intelligent respectant les frontières des fonctions et des classes via Tree-sitter.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-emerald-500/30 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4">
              <GitBranch className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Impact Analysis</h3>
            <p className="text-sm text-slate-400">
              Cartographie dynamique des dépendances et call graphs pour anticiper les risques de régression avant tout commit.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-emerald-500/30 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Zero-Execution & Grounding</h3>
            <p className="text-sm text-slate-400">
              Analyse 100% statique et sécurisée sans exécution de code, avec citations exactes de fichiers et numéros de lignes.
            </p>
          </div>
        </div>

        {/* System Diagnostics Card */}
        <div className="mt-12 p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-emerald-400" />
              <h2 className="text-md font-semibold text-white">Diagnostic Système (Phase 2 Initialisation)</h2>
            </div>
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> En direct
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 block text-xs">Service</span>
              <span className="font-mono text-emerald-400">{health?.service || 'DocuMind Backend'}</span>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 block text-xs">Statut API</span>
              <span className="font-mono text-white">{health?.status || (error ? 'Erreur de liaison' : 'Vérification...')}</span>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 block text-xs">Moteur Vectoriel</span>
              <span className="font-mono text-white">Qdrant (Port 6333)</span>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 block text-xs">Base de Données</span>
              <span className="font-mono text-white">PostgreSQL 16 (Port 5432)</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950 py-6 text-center text-xs text-slate-500">
        DocuMind — Projet de Fin d'Études en Génie Logiciel & Intelligence Artificielle. Architecture Clean & RAG Hybride.
      </footer>
    </div>
  );
};
