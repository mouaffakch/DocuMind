import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  FileText,
  Download,
  Copy,
  Check,
  Layers,
  Code2,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { docService } from '../services/api';
import { DocumentationResponse } from '../types/api';

export const DocumentationPage: React.FC = () => {
  const { activeProject } = useProject();
  const [loading, setLoading] = useState(false);
  const [docData, setDocData] = useState<DocumentationResponse | null>(null);
  const [modulePath, setModulePath] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateProjectOverview = async () => {
    if (!activeProject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await docService.generateProjectDoc(activeProject.id);
      setDocData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération de la documentation.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateUML = async () => {
    if (!activeProject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await docService.generateUMLDiagram(activeProject.id);
      setDocData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération du diagramme UML.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject || !modulePath.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await docService.generateModuleDoc(activeProject.id, modulePath.trim());
      setDocData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération de la documentation du module.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!docData) return;
    const blob = new Blob([docData.markdown_content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${activeProject?.name || 'project'}-documentation.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyMermaid = () => {
    if (!docData?.uml_diagram) return;
    navigator.clipboard.writeText(docData.uml_diagram);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!activeProject) {
    return (
      <div className="text-center py-24 bg-slate-900/40 border border-slate-800 rounded-2xl max-w-xl mx-auto p-8">
        <FileText className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-white">Aucun projet sélectionné</h2>
        <p className="text-xs text-slate-400 mt-1">
          Sélectionnez un projet pour générer la documentation technique et les diagrammes UML de classes.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-extrabold text-white">Génération Automatique de Documentation & UML</h1>
          <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-semibold">
            Markdown & Mermaid
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Générez une documentation technique complète, synthétisez les modules et visualisez les diagrammes de classes UML.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Generator Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Project Overview */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 w-fit mb-3">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Synthèse d'Architecture</h3>
            <p className="text-xs text-slate-400 mt-1">
              Vue d'ensemble complète du projet, des langages et des couches logicielles.
            </p>
          </div>
          <button
            onClick={handleGenerateProjectOverview}
            disabled={loading}
            className="mt-4 w-full py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
          >
            {loading ? 'Génération...' : 'Générer la Synthèse'}
          </button>
        </div>

        {/* UML Diagram */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 w-fit mb-3">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Diagramme de Classes UML</h3>
            <p className="text-xs text-slate-400 mt-1">
              Extrait les classes, méthodes, attributs et héritages au format Mermaid.
            </p>
          </div>
          <button
            onClick={handleGenerateUML}
            disabled={loading}
            className="mt-4 w-full py-2 px-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition disabled:opacity-50"
          >
            {loading ? 'Génération...' : 'Générer Diagramme UML'}
          </button>
        </div>

        {/* Module Guide */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 w-fit mb-3">
              <Code2 className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Documentation de Module</h3>
            <input
              type="text"
              value={modulePath}
              onChange={(e) => setModulePath(e.target.value)}
              placeholder="ex: app/services/auth.py"
              className="mt-2 w-full px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
          <button
            onClick={handleGenerateModule}
            disabled={loading || !modulePath.trim()}
            className="mt-4 w-full py-2 px-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white transition disabled:opacity-50"
          >
            {loading ? 'Génération...' : 'Documenter ce Module'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center justify-center space-y-2">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
          <span>Extraction des symboles AST et génération de la documentation Markdown...</span>
        </div>
      )}

      {/* Generated Documentation Viewer */}
      {docData && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-white">{docData.title}</h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                Type : {docData.doc_type}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleDownloadMarkdown}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
              >
                <Download className="h-3.5 w-3.5 text-indigo-400" />
                <span>Exporter en Markdown (.md)</span>
              </button>
            </div>
          </div>

          {/* UML Class Diagram Code block */}
          {docData.uml_diagram && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-purple-400">
                  Diagramme UML Mermaid
                </span>
                <button
                  onClick={handleCopyMermaid}
                  className="flex items-center space-x-1 text-xs text-slate-400 hover:text-white transition"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? 'Copié !' : 'Copier Mermaid'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-purple-300 overflow-x-auto shadow-inner">
                {docData.uml_diagram}
              </pre>
            </div>
          )}

          {/* Markdown Content */}
          <div className="prose prose-invert prose-sm max-w-none bg-slate-950/40 p-6 rounded-xl border border-slate-800/80">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {docData.markdown_content}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};
