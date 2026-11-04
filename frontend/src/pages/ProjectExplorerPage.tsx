import React, { useState, useEffect } from 'react';
import {
  FileCode2,
  Folder,
  Code,
  Search,
  Hash,
  Layers,
  AlertCircle,
  Loader2,
  FileText,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { projectService } from '../services/api';
import { CodeFile, CodeSymbol } from '../types/api';

export const ProjectExplorerPage: React.FC = () => {
  const { activeProject } = useProject();
  const [files, setFiles] = useState<CodeFile[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeProject) {
      setFiles([]);
      setSelectedFile(null);
      return;
    }

    const fetchFiles = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await projectService.listFiles(activeProject.id);
        setFiles(data);
        if (data.length > 0) {
          setSelectedFile(data[0]);
        } else {
          setSelectedFile(null);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Erreur lors de la récupération des fichiers du projet.');
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [activeProject]);

  const filteredFiles = files.filter((f) =>
    f.file_path.toLowerCase().includes(search.toLowerCase())
  );

  if (!activeProject) {
    return (
      <div className="text-center py-24 bg-slate-900/40 border border-slate-800 rounded-2xl max-w-xl mx-auto p-8">
        <Folder className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-white">Aucun projet sélectionné</h2>
        <p className="text-xs text-slate-400 mt-1">
          Sélectionnez un projet dans la barre latérale pour explorer son arborescence et ses symboles AST Tree-sitter.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-[calc(100vh-6rem)] flex flex-col">
      {/* Page Title */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-extrabold text-white">Explorateur de Code & AST</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-medium">
              {activeProject.name}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Naviguez dans les fichiers du dépôt et examinez les classes, méthodes et fonctions extraites par Tree-sitter.
          </p>
        </div>
        <div className="text-xs text-slate-400 font-mono">
          {files.length} fichiers répertoriés
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3 text-rose-300 text-sm shrink-0">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Explorer Container */}
      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Left Pane: Files List */}
        <div className="md:col-span-4 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
          <div className="p-3 border-b border-slate-800">
            <div className="relative">
              <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filtrer les fichiers..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/40">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-xs flex items-center justify-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                <span>Chargement de l'arborescence...</span>
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Aucun fichier trouvé.
              </div>
            ) : (
              filteredFiles.map((file) => {
                const isSelected = selectedFile?.id === file.id;
                return (
                  <button
                    key={file.id}
                    onClick={() => setSelectedFile(file)}
                    className={`w-full text-left px-3 py-2.5 text-xs flex items-center justify-between transition ${
                      isSelected
                        ? 'bg-indigo-600/20 text-indigo-200 border-l-2 border-indigo-500'
                        : 'text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileCode2 className={`h-4 w-4 shrink-0 ${isSelected ? 'text-indigo-400' : 'text-slate-500'}`} />
                      <span className="truncate font-mono">{file.file_path}</span>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono shrink-0 ml-1">
                      {file.language}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: File Details & AST Symbols */}
        <div className="md:col-span-8 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
          {selectedFile ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* File Header */}
              <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-2 truncate">
                  <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
                  <span className="font-mono text-xs font-semibold text-slate-200 truncate">
                    {selectedFile.file_path}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs shrink-0">
                  <span className="text-slate-400 font-mono">
                    {(selectedFile.size_bytes / 1024).toFixed(1)} KB
                  </span>
                  <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold uppercase text-[10px]">
                    {selectedFile.language}
                  </span>
                </div>
              </div>

              {/* AST Tree-sitter Symbols View */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <Layers className="h-4 w-4 text-purple-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Symboles AST Détectés (Tree-sitter)
                    </h3>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Fonctions, classes et interfaces extraites structurellement sans exécution.
                  </p>
                </div>

                {!selectedFile.symbols || selectedFile.symbols.length === 0 ? (
                  <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800/80 text-xs text-slate-500">
                    <Code className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    <p>Aucun symbole de haut niveau (classe/fonction) extrait pour ce fichier.</p>
                    <p className="text-[11px] text-slate-600 mt-1">
                      Le fichier peut contenir des constantes, de la configuration ou du balisage.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedFile.symbols.map((sym: CodeSymbol) => (
                      <div
                        key={sym.id}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase font-mono ${
                                sym.symbol_type === 'FUNCTION'
                                  ? 'bg-blue-500/20 text-blue-300'
                                  : sym.symbol_type === 'CLASS'
                                  ? 'bg-purple-500/20 text-purple-300'
                                  : 'bg-emerald-500/20 text-emerald-300'
                              }`}
                            >
                              {sym.symbol_type}
                            </span>
                            <span className="font-mono text-sm font-bold text-white">
                              {sym.name}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                            <Hash className="h-3 w-3 text-slate-500" />
                            <span>Lignes {sym.start_line} - {sym.end_line}</span>
                          </span>
                        </div>

                        {sym.signature && (
                          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
                            <code>{sym.signature}</code>
                          </div>
                        )}

                        {sym.docstring && (
                          <p className="text-xs text-slate-400 italic bg-slate-900/40 p-2 rounded border border-slate-800/40">
                            {sym.docstring}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500 text-xs">
              <FileCode2 className="h-10 w-10 text-slate-600 mb-2" />
              <span>Sélectionnez un fichier dans la colonne de gauche</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
