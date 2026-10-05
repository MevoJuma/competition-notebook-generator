import { Link } from 'react-router-dom';
import { Upload, BarChart3, BookOpen, ArrowRight, Zap, Shield, Target } from 'lucide-react';

const STATS = [
  { icon: '🏆', value: '28', label: 'Tests Passing' },
  { icon: '⚡', value: '9', label: 'Phases Complete' },
  { icon: '🤖', value: 'GPT-4', label: 'AI Engine' },
  { icon: '📊', value: 'DuckDB', label: 'Data Profiler' },
];

const PIPELINE_STEPS = [
  { step: 1, title: 'Upload Competition Files', desc: 'CSV datasets, PDFs, ZIP archives', status: 'done' },
  { step: 2, title: 'Document Analysis', desc: 'Extract rules, metrics, and target hints', status: 'done' },
  { step: 3, title: 'Data Profiling', desc: 'Schema reconciliation & drift detection', status: 'done' },
  { step: 4, title: 'Task Classification', desc: 'Problem type, metric & CV strategy', status: 'done' },
  { step: 5, title: 'AI Orchestration', desc: 'LLM synthesizes notebook plan', status: 'active' },
  { step: 6, title: 'Notebook Generation', desc: 'Production-ready .ipynb bundle', status: 'idle' },
];

const FEATURES = [
  {
    icon: <Zap size={20} />,
    title: 'Zero Hallucination',
    desc: 'Every fact is extracted from actual data. No guessing — pure signal.',
  },
  {
    icon: <Shield size={20} />,
    title: 'Leakage Detection',
    desc: 'Automatically flags ID overlap and target contamination between splits.',
  },
  {
    icon: <Target size={20} />,
    title: 'Multi-Signal Classification',
    desc: 'Combines NLP, schema analysis, and profiling to classify problem type.',
  },
];

export default function HomePage() {
  return (
    <div className="page animate-fade-in">
      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">
          <Zap size={10} /> AI-Powered Competition Platform
        </div>
        <h1 className="hero-title">
          From raw data to{' '}
          <span className="hero-title-gradient">production notebook</span>
          {' '}in minutes.
        </h1>
        <p className="hero-description">
          Upload your Zindi or Kaggle competition files and let the AI analyze, profile, classify,
          and generate a fully-verified, competition-ready Jupyter notebook — automatically.
        </p>
        <div className="flex gap-3">
          <Link to="/upload" className="btn btn-primary btn-lg">
            <Upload size={18} /> Start Now
          </Link>
          <Link to="/analysis" className="btn btn-secondary btn-lg">
            <BarChart3 size={18} /> View Analysis
          </Link>
        </div>
      </section>

      {/* Stats */}
      <div className="stats-grid animate-fade-in-1">
        {STATS.map((s) => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2 gap-4 animate-fade-in-2" style={{ alignItems: 'start' }}>
        {/* Pipeline */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Analysis Pipeline</div>
              <div className="card-subtitle">Current processing status</div>
            </div>
            <span className="badge badge-purple">Live</span>
          </div>
          <div className="pipeline">
            {PIPELINE_STEPS.map((s) => (
              <div key={s.step} className={`pipeline-step ${s.status}`}>
                <div className="pipeline-step-number">
                  {s.status === 'done' ? '✓' : s.step}
                </div>
                <div className="pipeline-step-content">
                  <div className="pipeline-step-title">{s.title}</div>
                  <div className="pipeline-step-desc">{s.desc}</div>
                </div>
                {s.status === 'active' && <div className="spinner" />}
              </div>
            ))}
          </div>
        </div>

        {/* Features + CTA */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {FEATURES.map((f) => (
            <div key={f.title} className="card">
              <div className="flex gap-3 items-center mb-4">
                <div style={{
                  width: 36, height: 36, borderRadius: 'var(--radius-md)',
                  background: 'rgba(99,102,241,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--color-text-accent)',
                }}>
                  {f.icon}
                </div>
                <div className="card-title">{f.title}</div>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                {f.desc}
              </p>
            </div>
          ))}

          <Link to="/notebook" className="btn btn-primary" style={{ justifyContent: 'center', padding: 'var(--space-4)' }}>
            <BookOpen size={16} /> Open Notebook Studio <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </div>
  );
}
