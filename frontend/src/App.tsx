import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, BarChart3, BookOpen, Settings, Zap } from 'lucide-react';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import NotebookPage from './pages/NotebookPage';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload Files' },
  { to: '/analysis', icon: BarChart3, label: 'Analysis' },
  { to: '/notebook', icon: BookOpen, label: 'Notebook Studio' },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-logo">
          <div className="sidebar-brand-icon">⚡</div>
          <div>
            <div className="sidebar-brand-name">NotebookAI</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Competition Platform</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}

        <div className="sidebar-section-label" style={{ marginTop: 'auto' }}>System</div>
        <div className="sidebar-nav-item" style={{ cursor: 'default' }}>
          <Settings size={16} />
          Settings
        </div>
      </nav>

      <div style={{ padding: 'var(--space-4) var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
        <div style={{
          background: 'rgba(99,102,241,0.1)',
          border: '1px solid rgba(99,102,241,0.25)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)', color: 'var(--color-text-accent)', fontWeight: 600 }}>
            <Zap size={12} /> AI Engine Ready
          </div>
          <div style={{ color: 'var(--color-text-muted)' }}>GPT-4 Turbo connected</div>
        </div>
      </div>
    </aside>
  );
}

function Topbar() {
  const location = useLocation();
  const titles: Record<string, { title: string; subtitle: string }> = {
    '/': { title: 'Dashboard', subtitle: 'Overview of your competition projects' },
    '/upload': { title: 'Upload Files', subtitle: 'Import competition data and documentation' },
    '/analysis': { title: 'Intelligence Analysis', subtitle: 'AI-powered competition profiling' },
    '/notebook': { title: 'Notebook Studio', subtitle: 'Generate and download your starter notebook' },
  };
  const meta = titles[location.pathname] ?? { title: 'NotebookAI', subtitle: '' };
  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">{meta.title}</div>
        {meta.subtitle && <div className="topbar-subtitle">{meta.subtitle}</div>}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <div className="main-content">
          <Topbar />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/notebook" element={<NotebookPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
