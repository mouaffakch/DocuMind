import React, { useState } from 'react';
import {
  Bug,
  AlertCircle,
  CheckCircle2,
  ShieldAlert,
  TestTube2,
  Wrench,
  HelpCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { bugAnalysisService } from '../services/api';
import { BugAnalysisResponse } from '../types/api';

export const BugAnalysisPage: React.FC = () => {
  const { activeProject } = useProject();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [stacktrace, setStacktrace] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<BugAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedCitationId, setExpandedCitationId] = useState<string | null>(null);

  const handleDiagnose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject || !title.trim() || !description.trim()) return;

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const data = await bugAnalysisService.analyze(activeProject.id, {
        title: title.trim(),
        description: description.trim(),
        stacktrace: stacktrace.trim() || undefined,
      });
      setAnalysis(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du diagnostic du bug.');
    } finally {
      setLoading(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="text-center py-24 bg-slate-900/40 border border-slate-800 rounded-2xl max-w-xl mx-auto p-8">
        <Bug className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-white">Aucun projet sélectionné</h2>
        <p className="text-xs text-slate-400 mt-1">
          Sélectionnez un projet pour corréler les descriptions de bug et les stacktraces avec le code source.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-extrabold text-white">Triage & Analyse des Bugs</h1>
          <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold">
            Diagnostic Non-Dogmatique
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Isolez les fonctions suspectes, formulez des hypothèses explicites et obtenez des recommandations de correctifs vérifiables.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Bug Submission Form */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl">
        <form onSubmit={handleDiagnose} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Titre du Bug ou de l'Issue GitHub
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Erreur 401 inattendue lors du renouvellement de token JWT"
              className="w-full px-3.5 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Description du Comportement Constaté
            </label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Décrivez les étapes pour reproduire le bug, les paramètres envoyés et le comportement erratique..."
              className="w-full px-3.5 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Trace d'Erreur (Stacktrace optionnelle)
            </label>
            <textarea
              rows={4}
              value={stacktrace}
              onChange={(e) => setStacktrace(e.target.value)}
              placeholder={'Traceback (most recent call last):\n  File "src/auth/jwt.py", line 55, in verify_jwt_token\n    raise JWTError("Signature expired")'}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-slate-300 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !title.trim() || !description.trim()}
            className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-gradient-to-r from-rose-600 to-indigo-600 hover:from-rose-500 hover:to-indigo-500 text-xs font-bold text-white shadow-lg shadow-rose-600/20 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                <span>Recherche hybride et analyse du diagnostic...</span>
              </>
            ) : (
              <>
                <Bug className="h-4 w-4" />
                <span>Diagnostiquer l'incident</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Analysis Results View */}
      {analysis && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Diagnostic Summary */}
          <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              <span>{analysis.problem_summary}</span>
            </h2>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="text-slate-400">Fichiers corrélés :</span>
              {analysis.identified_files.length === 0 ? (
                <span className="text-slate-500">Aucun fichier directement corrélé</span>
              ) : (
                analysis.identified_files.map((f, i) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                    {f}
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Suspect Functions */}
          {analysis.suspect_functions.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Composants / Fonctions Suspects
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {analysis.suspect_functions.map((s, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase font-mono ${
                            s.suspicion_level === 'HIGH'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : s.suspicion_level === 'MEDIUM'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          Niveau {s.suspicion_level}
                        </span>
                        <span className="font-mono text-sm font-bold text-white">{s.name}</span>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono block mt-1">
                        {s.file_path} ({s.lines})
                      </span>
                      <p className="text-xs text-slate-300 mt-2">{s.rationale}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hypothetical Causes */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <div className="flex items-center space-x-2">
              <HelpCircle className="h-5 w-5 text-indigo-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Hypothèses de Causes (Non-Dogmatiques)
              </h3>
            </div>
            <ul className="space-y-2 text-xs text-slate-300">
              {analysis.hypothetical_causes.map((cause, idx) => (
                <li key={idx} className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80">
                  {cause}
                </li>
              ))}
            </ul>
          </div>

          {/* Suggested Fixes and Recommended Tests */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fixes */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
              <div className="flex items-center space-x-2">
                <Wrench className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Pistes de Correction
                </h3>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                {analysis.suggested_fixes.map((fix, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/20">
                    {fix}
                  </li>
                ))}
              </ul>
            </div>

            {/* Tests */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
              <div className="flex items-center space-x-2">
                <TestTube2 className="h-5 w-5 text-purple-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Tests Recommandés
                </h3>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                {analysis.recommended_tests.map((test, idx) => (
                  <li key={idx} className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/20">
                    {test}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Grounded Citations */}
          {analysis.citations.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Extraits de Code Sources Corrélés ({analysis.citations.length})
              </h3>
              <div className="space-y-2">
                {analysis.citations.map((cite) => {
                  const isExp = expandedCitationId === cite.id;
                  return (
                    <div key={cite.id} className="border border-slate-800 rounded-xl overflow-hidden">
                      <button
                        onClick={() => setExpandedCitationId(isExp ? null : cite.id)}
                        className="w-full text-left p-3 bg-slate-950/60 hover:bg-slate-950 flex items-center justify-between text-xs transition"
                      >
                        <span className="font-mono text-indigo-400">
                          {cite.file_path}:L{cite.start_line}-L{cite.end_line}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-[10px] text-slate-400">
                            Pertinence : {(cite.relevance_score * 100).toFixed(0)}%
                          </span>
                          {isExp ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </div>
                      </button>
                      {isExp && (
                        <div className="p-3 bg-slate-950 font-mono text-[11px] text-slate-300 whitespace-pre-wrap overflow-x-auto border-t border-slate-800">
                          {cite.code_snippet}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
