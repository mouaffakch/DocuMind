import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  MessageSquareCode,
  Send,
  Plus,
  Bot,
  User,
  FileCode,
  Sparkles,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { chatService } from '../services/api';
import { ChatSession, ChatMessage } from '../types/api';

export const ChatPage: React.FC = () => {
  const { activeProject } = useProject();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [loadingSessions, setLoadingSessions] = useState<boolean>(false);
  const [expandedSnippetId, setExpandedSnippetId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  // Load chat sessions when active project changes
  useEffect(() => {
    if (!activeProject) {
      setSessions([]);
      setCurrentSessionId(null);
      setMessages([]);
      return;
    }

    const loadSessions = async () => {
      setLoadingSessions(true);
      setError(null);
      try {
        const data = await chatService.listSessions(activeProject.id);
        setSessions(data);
        if (data.length > 0) {
          setCurrentSessionId(data[0].id);
        } else {
          // Auto create first session
          const newSession = await chatService.createSession(activeProject.id, 'Discussion Générale');
          setSessions([newSession]);
          setCurrentSessionId(newSession.id);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Erreur lors du chargement des sessions.');
      } finally {
        setLoadingSessions(false);
      }
    };

    loadSessions();
  }, [activeProject]);

  // Load messages for current session
  useEffect(() => {
    if (!activeProject || !currentSessionId) {
      setMessages([]);
      return;
    }

    const fetchSessionDetails = async () => {
      try {
        const session = await chatService.getSession(activeProject.id, currentSessionId);
        setMessages(session.messages || []);
      } catch (err: any) {
        console.error('Failed to load session messages:', err);
      }
    };

    fetchSessionDetails();
  }, [activeProject, currentSessionId]);

  const handleCreateSession = async () => {
    if (!activeProject) return;
    try {
      const newSession = await chatService.createSession(activeProject.id, `Session ${sessions.length + 1}`);
      setSessions([newSession, ...sessions]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Impossible de créer une nouvelle session.');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeProject || !currentSessionId || sending) return;

    const userText = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Optimistic user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId,
      role: 'USER',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const assistantMsg = await chatService.sendMessage(activeProject.id, currentSessionId, userText);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Échec de la réponse du chatbot IA.');
    } finally {
      setSending(false);
    }
  };

  const handleSuggestedPrompt = (promptText: string) => {
    setInputMessage(promptText);
  };

  if (!activeProject) {
    return (
      <div className="text-center py-24 bg-slate-900/40 border border-slate-800 rounded-2xl max-w-xl mx-auto p-8">
        <MessageSquareCode className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-white">Aucun projet sélectionné</h2>
        <p className="text-xs text-slate-400 mt-1">
          Sélectionnez un projet dans le sélecteur pour démarrer une conversation RAG avec le code source.
        </p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col md:flex-row gap-5 max-w-7xl mx-auto">
      {/* Sessions Sidebar */}
      <div className="w-full md:w-64 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col shrink-0 overflow-hidden">
        <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Conversations
          </span>
          <button
            onClick={handleCreateSession}
            className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition text-xs flex items-center space-x-1"
            title="Nouvelle conversation"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="text-[11px] font-semibold pr-1">Nouveau</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loadingSessions ? (
            <div className="p-4 text-center text-xs text-slate-500 flex items-center justify-center space-x-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>Chargement...</span>
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">Aucune conversation</div>
          ) : (
            sessions.map((sess) => {
              const isSelected = sess.id === currentSessionId;
              return (
                <button
                  key={sess.id}
                  onClick={() => setCurrentSessionId(sess.id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition ${
                    isSelected
                      ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                      : 'text-slate-300 hover:bg-slate-800/80'
                  }`}
                >
                  <span className="truncate">{sess.title}</span>
                  <span className={`text-[10px] ${isSelected ? 'text-indigo-200' : 'text-slate-500'}`}>
                    {new Date(sess.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-white">Assistant Code DocuMind</h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  RAG Hybrid + AST
                </span>
              </div>
              <span className="text-[11px] text-slate-400">Projet : {activeProject.name}</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border-b border-rose-500/20 flex items-center space-x-2 text-rose-300 text-xs">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-5 max-w-lg mx-auto">
              <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Interrogez le code de {activeProject.name}</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Chaque réponse est ancrée dans le code source réel avec références de fichiers et lignes exactes.
                </p>
              </div>

              {/* Suggested Prompts Pills */}
              <div className="w-full space-y-2 pt-2">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Questions suggérées :
                </span>
                <button
                  onClick={() => handleSuggestedPrompt("Comment fonctionne l'architecture globale de ce projet ?")}
                  className="w-full text-left p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 text-xs text-slate-300 transition"
                >
                  📐 "Comment fonctionne l'architecture globale de ce projet ?"
                </button>
                <button
                  onClick={() => handleSuggestedPrompt("Où se trouve la fonction responsable de la gestion des utilisateurs et de l'authentification ?")}
                  className="w-full text-left p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 text-xs text-slate-300 transition"
                >
                  🔐 "Où se trouve la fonction responsable de l'authentification ?"
                </button>
                <button
                  onClick={() => handleSuggestedPrompt("Quels tests dois-je exécuter si je modifie les modèles de données ?")}
                  className="w-full text-left p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 text-xs text-slate-300 transition"
                >
                  🧪 "Quels tests dois-je exécuter si je modifie les modèles de données ?"
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'USER' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role !== 'USER' && (
                  <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-sm mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 text-xs ${
                    msg.role === 'USER'
                      ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/20'
                      : 'bg-slate-950/80 border border-slate-800 text-slate-200'
                  }`}
                >
                  {/* Message Content with Markdown rendering */}
                  <div className="prose prose-invert prose-xs max-w-none space-y-2 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Grounded Citations & Sources Badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
                      <div className="flex items-center space-x-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        <FileCode className="h-3 w-3 text-indigo-400" />
                        <span>Sources et Citations Vérifiées ({msg.citations.length})</span>
                      </div>

                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((cite) => {
                          const isExpanded = expandedSnippetId === cite.id;
                          return (
                            <div key={cite.id} className="w-full">
                              <button
                                onClick={() =>
                                  setExpandedSnippetId(isExpanded ? null : cite.id)
                                }
                                className="flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] text-slate-300 font-mono transition"
                              >
                                <div className="flex items-center space-x-1.5 truncate">
                                  <span className="text-indigo-400 font-bold">{cite.file_path}</span>
                                  <span className="text-slate-500">
                                    :L{cite.start_line}-L{cite.end_line}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2 shrink-0 ml-2">
                                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                    {(cite.relevance_score * 100).toFixed(0)}%
                                  </span>
                                  {isExpanded ? (
                                    <ChevronUp className="h-3 w-3 text-slate-400" />
                                  ) : (
                                    <ChevronDown className="h-3 w-3 text-slate-400" />
                                  )}
                                </div>
                              </button>

                              {isExpanded && (
                                <div className="mt-1 p-2.5 rounded-lg bg-slate-900/95 border border-slate-800 font-mono text-[11px] text-slate-300 whitespace-pre-wrap overflow-x-auto shadow-inner">
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

                {msg.role === 'USER' && (
                  <div className="h-8 w-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {sending && (
            <div className="flex gap-3 justify-start">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shrink-0 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center space-x-3 text-xs text-slate-400">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                <span>Recherche sémantique, reranking et génération de la réponse...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800 bg-slate-950/50 flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={sending}
            placeholder={`Posez une question sur le projet ${activeProject.name}...`}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={sending || !inputMessage.trim()}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition shrink-0"
          >
            <Send className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Envoyer</span>
          </button>
        </form>
      </div>
    </div>
  );
};
