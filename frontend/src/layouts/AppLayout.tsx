import React, { useState } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  GitPullRequest,
  MessageSquareCode,
  FileCode2,
  Network,
  Bug,
  FileText,
  Settings,
  LogOut,
  ChevronDown,
  Layers,
  Sparkles,
  Menu,
  X,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useProject } from '../contexts/ProjectContext';

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { projects, activeProject, setActiveProject } = useProject();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Mes Projets', href: '/projects', icon: FolderGit2 },
    { name: 'Importer un Dépôt', href: '/import', icon: GitPullRequest },
    { name: 'Chatbot IA & RAG', href: '/chat', icon: MessageSquareCode, badge: 'IA' },
    { name: 'Explorateur de Code', href: '/explorer', icon: FileCode2 },
    { name: 'Impact Analysis', href: '/impact', icon: Network, badge: 'AST' },
    { name: 'Analyse des Bugs', href: '/bugs', icon: Bug },
    { name: 'Documentation & UML', href: '/docs', icon: FileText },
    { name: 'Paramètres', href: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row antialiased selection:bg-indigo-500 selection:text-white">
      {/* Mobile Top Header */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            DM
          </div>
          <span className="font-bold text-lg text-white">DocuMind</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-slate-400 hover:text-white focus:outline-none"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:flex flex-col w-full md:w-64 bg-slate-900/90 backdrop-blur-xl border-r border-slate-800 shrink-0 z-30 transition-all duration-300`}
      >
        {/* Brand Logo & Tag */}
        <div className="p-5 border-b border-slate-800/80 hidden md:flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                DocuMind
              </span>
              <span className="block text-[10px] font-medium tracking-wider uppercase text-indigo-400">
                Code Intelligence
              </span>
            </div>
          </Link>
        </div>

        {/* Project Selector Badge */}
        <div className="px-4 py-3 border-b border-slate-800/80 bg-slate-950/40">
          <div className="relative">
            <button
              onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
              className="w-full flex items-center justify-between px-3 py-2 text-left rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 transition shadow-sm text-xs"
            >
              <div className="truncate">
                <span className="block text-[10px] text-slate-400 uppercase font-semibold">Projet Actif</span>
                <span className="font-medium text-slate-200 truncate">
                  {activeProject ? activeProject.name : 'Aucun projet sélectionné'}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400 shrink-0 ml-1" />
            </button>

            {projectDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1.5 bg-slate-800 border border-slate-700 rounded-lg shadow-xl py-1 z-50 max-h-56 overflow-y-auto">
                {projects.length === 0 ? (
                  <div className="p-3 text-center text-xs text-slate-400">
                    Aucun projet disponible.
                    <Link
                      to="/import"
                      onClick={() => setProjectDropdownOpen(false)}
                      className="block mt-1.5 text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      + Importer un dépôt
                    </Link>
                  </div>
                ) : (
                  projects.map((proj) => (
                    <button
                      key={proj.id}
                      onClick={() => {
                        setActiveProject(proj);
                        setProjectDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-700/80 transition ${
                        activeProject?.id === proj.id ? 'bg-indigo-600/20 text-indigo-300 font-semibold' : 'text-slate-300'
                      }`}
                    >
                      <span className="truncate">{proj.name}</span>
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                          proj.status === 'READY'
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : proj.status === 'INDEXING'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-rose-500/20 text-rose-300'
                        }`}
                      >
                        {proj.status}
                      </span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`h-4 w-4 transition-colors ${
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${
                      isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-indigo-400 border border-indigo-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 truncate">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center font-bold text-xs text-white uppercase shrink-0">
                {user?.full_name ? user.full_name[0] : 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-medium text-slate-200 truncate">{user?.full_name || 'Utilisateur'}</p>
                <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Déconnexion"
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md hover:bg-slate-800/60 transition"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Project Warning Bar when on project-dependent routes without active project */}
        {!activeProject &&
          ['/chat', '/explorer', '/impact', '/bugs', '/docs'].includes(location.pathname) && (
            <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center justify-between text-xs text-amber-200">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-4 w-4 text-amber-400" />
                <span>
                  Aucun projet sélectionné. Veuillez importer ou choisir un projet pour exploiter les capacités IA et AST.
                </span>
              </div>
              <Link
                to="/import"
                className="font-medium text-amber-400 underline hover:text-amber-300 flex items-center space-x-1"
              >
                <span>Importer un projet</span>
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          )}

        <div className="flex-1 p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
