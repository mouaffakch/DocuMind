import React, { useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Network,
  Search,
  ShieldCheck,
  ShieldAlert,
  TestTube2,
  Layers,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { impactService } from '../services/api';
import { ImpactAnalysisResponse } from '../types/api';

export const ImpactAnalysisPage: React.FC = () => {
  const { activeProject } = useProject();
  const [query, setQuery] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [loading, setLoading] = useState(false);
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<any[]>([]);
  const [impactData, setImpactData] = useState<ImpactAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Autocomplete symbol search
  const handleQueryChange = async (val: string) => {
    setQuery(val);
    if (!activeProject || val.length < 2) {
      setAutocompleteSuggestions([]);
      return;
    }
    try {
      const suggestions = await impactService.autocompleteSymbols(activeProject.id, val);
      setAutocompleteSuggestions(suggestions);
    } catch {
      // Ignore autocomplete failures silently
    }
  };

  const handleSelectSuggestion = (name: string) => {
    setQuery(name);
    setAutocompleteSuggestions([]);
    executeAnalysis(name);
  };

  const executeAnalysis = async (symbolToAnalyze?: string) => {
    const sym = symbolToAnalyze || query;
    if (!activeProject || !sym.trim()) return;

    setLoading(true);
    setError(null);
    setAutocompleteSuggestions([]);

    try {
      const res = await impactService.analyze(activeProject.id, sym.trim(), maxDepth);
      setImpactData(res);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          `Aucun appelant direct trouvé pour "${sym}". Vérifiez l'orthographe du symbole.`
      );
      setImpactData(null);
    } finally {
      setLoading(false);
    }
  };

  // Convert ImpactGraph nodes and edges to ReactFlow format
  const getFlowElements = (): { nodes: Node[]; edges: Edge[] } => {
    if (!impactData || !impactData.nodes) return { nodes: [], edges: [] };

    const flowNodes: Node[] = impactData.nodes.map((n, idx) => {
      const isTarget = n.label === impactData.target_symbol;
      const xPos = 200 + (n.depth * 250);
      const yPos = 80 + (idx * 90);

      return {
        id: n.id,
        position: { x: xPos, y: yPos },
        data: {
          label: (
            <div
              className={`p-3 rounded-xl border text-xs shadow-md transition ${
                isTarget
                  ? 'bg-indigo-950 border-indigo-500 text-white font-bold ring-2 ring-indigo-500/50'
                  : n.is_test
                  ? 'bg-emerald-950/80 border-emerald-500/80 text-emerald-200'
                  : 'bg-slate-900 border-slate-700 text-slate-200'
              }`}
            >
              <div className="flex items-center space-x-1.5 mb-1">
                {n.is_test ? (
                  <TestTube2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                ) : (
                  <Layers className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                )}
                <span className="font-mono font-semibold truncate">{n.label}</span>
              </div>
              <span className="text-[10px] text-slate-400 block truncate font-mono">
                {n.file_path}
              </span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400 mt-1 inline-block">
                Profondeur : {n.depth}
              </span>
            </div>
          ),
        },
      };
    });

    const flowEdges: Edge[] = (impactData.edges || []).map((e, idx) => ({
      id: `edge-${idx}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#6366f1',
      },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  };

  const { nodes, edges } = getFlowElements();

  if (!activeProject) {
    return (
      <div className="text-center py-24 bg-slate-900/40 border border-slate-800 rounded-2xl max-w-xl mx-auto p-8">
        <Network className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-white">Aucun projet sélectionné</h2>
        <p className="text-xs text-slate-400 mt-1">
          Sélectionnez un projet pour analyser les dépendances statiques et calculer le risque de régression.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-extrabold text-white">Impact Analysis & Graphe d'Appels</h1>
          <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-semibold">
            AST Static Analysis
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Évaluez les conséquences d'une modification de fonction ou méthode avant de toucher au code.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Query Bar */}
      <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-xl relative">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder="Ex: authenticate_user, verify_token, calculate_total..."
              className="block w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 text-xs placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />

            {/* Autocomplete Dropdown */}
            {autocompleteSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl py-1 z-50 max-h-56 overflow-y-auto">
                {autocompleteSuggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectSuggestion(s.name)}
                    className="w-full text-left px-3.5 py-2 hover:bg-slate-700 flex items-center justify-between text-xs transition"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-semibold text-slate-200">{s.name}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-900 text-slate-400 font-mono">
                        {s.symbol_type}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono truncate max-w-xs">
                      {s.file_path}:L{s.line}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <label className="text-xs text-slate-400">Profondeur max :</label>
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={1}>1 (Appelants directs)</option>
              <option value={2}>2 (Transitif moyen)</option>
              <option value={3}>3 (Analyse profonde)</option>
              <option value={5}>5 (Système complet)</option>
            </select>
          </div>

          <button
            onClick={() => executeAnalysis()}
            disabled={loading || !query.trim()}
            className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-semibold text-white shadow-lg shadow-purple-600/20 transition disabled:opacity-50 shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                <span>Traversée BFS...</span>
              </>
            ) : (
              <>
                <Network className="h-4 w-4" />
                <span>Calculer l'impact</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Results */}
      {impactData && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Risk Assessment Card */}
          <div
            className={`p-6 rounded-2xl border shadow-xl ${
              impactData.risk_assessment.level === 'CRITICAL'
                ? 'bg-rose-950/40 border-rose-500/40 text-rose-200'
                : impactData.risk_assessment.level === 'HIGH'
                ? 'bg-amber-950/40 border-amber-500/40 text-amber-200'
                : impactData.risk_assessment.level === 'MEDIUM'
                ? 'bg-yellow-950/40 border-yellow-500/40 text-yellow-200'
                : 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
            }`}
          >
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  {impactData.risk_assessment.level === 'CRITICAL' ||
                  impactData.risk_assessment.level === 'HIGH' ? (
                    <ShieldAlert className="h-6 w-6 text-rose-400" />
                  ) : (
                    <ShieldCheck className="h-6 w-6 text-emerald-400" />
                  )}
                  <h3 className="text-lg font-bold">
                    Niveau de Risque : {impactData.risk_assessment.level}
                  </h3>
                </div>
                <p className="text-xs mt-1 max-w-2xl text-slate-300">
                  {impactData.risk_assessment.explanation}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center shrink-0">
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="block text-[10px] uppercase font-semibold text-slate-400">Appels Directs</span>
                  <span className="text-lg font-mono font-bold text-white">
                    {impactData.risk_assessment.direct_callers_count}
                  </span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="block text-[10px] uppercase font-semibold text-slate-400">Transitifs</span>
                  <span className="text-lg font-mono font-bold text-white">
                    {impactData.risk_assessment.transitive_callers_count}
                  </span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="block text-[10px] uppercase font-semibold text-slate-400">Tests à Relancer</span>
                  <span className="text-lg font-mono font-bold text-emerald-400">
                    {impactData.affected_tests.length}
                  </span>
                </div>
              </div>
            </div>

            {/* Affected Tests List */}
            {impactData.affected_tests.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-800/80">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5 mb-2">
                  <TestTube2 className="h-4 w-4 text-emerald-400" />
                  <span>Suites de Tests Automatisés à Revalider :</span>
                </span>
                <div className="flex flex-wrap gap-2">
                  {impactData.affected_tests.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-emerald-300"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Interactive ReactFlow Dependency Graph */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="flex items-center justify-between mb-3 px-2">
              <div className="flex items-center space-x-2">
                <Network className="h-4 w-4 text-indigo-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Graphe Interactif des Dépendances
                </h3>
              </div>
              <span className="text-[11px] text-slate-500">
                Zoom, pan et déplacez les nœuds pour inspecter la propagation
              </span>
            </div>

            <div className="h-[480px] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
              >
                <Background color="#334155" gap={16} />
                <Controls />
              </ReactFlow>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
