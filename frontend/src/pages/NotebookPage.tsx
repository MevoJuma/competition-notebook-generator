import { useState } from 'react';
import { BookOpen, Download, CheckCircle, AlertCircle, Loader, Sparkles } from 'lucide-react';

const MOCK_PLAN = {
  competition_title: 'Financial Inclusion in Africa',
  problem_type: 'Binary Classification',
  evaluation_metric: 'ROC-AUC',
  target_variable: 'bank_account',
  validation_strategy: 'StratifiedKFold (5 folds)',
  feature_engineering_ideas: [
    {
      feature_name: 'Age Group Buckets',
      description: 'Bin age into meaningful demographic segments to improve generalization.',
      code_snippet: "df['age_group'] = pd.cut(df['age_of_respondent'], bins=[0,25,35,50,65,100], labels=['youth','young_adult','middle','senior','elderly'])",
    },
    {
      feature_name: 'Household Size Interaction',
      description: 'Cross-feature capturing family financial burden vs. cellphone access.',
      code_snippet: "df['hh_cell_interaction'] = df['household_size'] * (df['cellphone_access'] == 'Yes').astype(int)",
    },
    {
      feature_name: 'Country-Year Encoding',
      description: 'Capture temporal trends within each country separately.',
      code_snippet: "df['country_year'] = df['country'].astype(str) + '_' + df['year'].astype(str)",
    },
  ],
  model_strategy: {
    models_to_train: ['LightGBM', 'CatBoost', 'XGBoost'],
    ensemble_method: 'Weighted Average (rank-based)',
  },
};

type TabId = 'plan' | 'features' | 'models';

export default function NotebookPage() {
  const [activeTab, setActiveTab] = useState<TabId>('plan');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => { setGenerating(false); setGenerated(true); }, 2000);
  };

  const TABS: { id: TabId; label: string }[] = [
    { id: 'plan', label: 'Plan Overview' },
    { id: 'features', label: 'Feature Engineering' },
    { id: 'models', label: 'Model Strategy' },
  ];

  return (
    <div className="page animate-fade-in">
      <div className="grid-2 animate-fade-in" style={{ gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Left: plan viewer */}
        <div>
          {/* Tabs */}
          <div style={{
            display: 'flex',
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-1)',
            gap: 'var(--space-1)',
            marginBottom: 'var(--space-5)',
          }}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  flex: 1,
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  background: activeTab === tab.id ? 'rgba(99,102,241,0.2)' : 'transparent',
                  color: activeTab === tab.id ? 'var(--color-text-accent)' : 'var(--color-text-secondary)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all var(--transition-base)',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Plan Overview */}
          {activeTab === 'plan' && (
            <div className="card animate-fade-in">
              <div className="card-title mb-4">{MOCK_PLAN.competition_title}</div>
              {[
                { label: 'Problem Type', value: MOCK_PLAN.problem_type },
                { label: 'Target Variable', value: MOCK_PLAN.target_variable },
                { label: 'Evaluation Metric', value: MOCK_PLAN.evaluation_metric },
                { label: 'Validation Strategy', value: MOCK_PLAN.validation_strategy },
              ].map((row) => (
                <div key={row.label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: 'var(--space-3) 0',
                  borderBottom: '1px solid var(--color-border)',
                }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{row.label}</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{row.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Feature Engineering */}
          {activeTab === 'features' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }} className="animate-fade-in">
              {MOCK_PLAN.feature_engineering_ideas.map((feat, i) => (
                <div key={i} className="card">
                  <div className="flex gap-2 items-center mb-4">
                    <Sparkles size={14} color="var(--color-text-accent)" />
                    <div className="card-title" style={{ fontSize: '0.9rem' }}>{feat.feature_name}</div>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                    {feat.description}
                  </p>
                  <div className="code-block">{feat.code_snippet}</div>
                </div>
              ))}
            </div>
          )}

          {/* Models */}
          {activeTab === 'models' && (
            <div className="card animate-fade-in">
              <div className="card-title mb-4">Modeling Strategy</div>
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginBottom: 'var(--space-5)' }}>
                {MOCK_PLAN.model_strategy.models_to_train.map((m) => (
                  <span key={m} className="badge badge-purple" style={{ fontSize: '0.8rem', padding: '4px 10px' }}>{m}</span>
                ))}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
                Ensemble Method
              </div>
              <div style={{ fontWeight: 600 }}>{MOCK_PLAN.model_strategy.ensemble_method}</div>
              <div className="divider" />
              <div className="alert alert-info">
                <BookOpen size={14} style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '0.8rem' }}>
                  Each model is trained in a 5-fold CV loop. OOF predictions are blended using rank averaging.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Right: generate + download panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className={`card ${generated ? 'animate-pulse-glow' : ''}`} style={{ borderColor: generated ? 'rgba(16,185,129,0.4)' : undefined }}>
            <div className="card-title mb-4">Notebook Generation</div>

            {!generated ? (
              <>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-5)' }}>
                  Click below to generate a fully-validated, production-ready Jupyter notebook
                  from the current plan. The notebook will be validated for syntax and imports
                  before packaging.
                </p>
                <button
                  id="generate-notebook-btn"
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={handleGenerate}
                  disabled={generating}
                >
                  {generating ? <><div className="spinner" /> Generating…</> : <><Sparkles size={16} /> Generate Notebook</>}
                </button>
              </>
            ) : (
              <>
                <div className="alert alert-success mb-4">
                  <CheckCircle size={16} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Notebook ready!</strong>
                    <div style={{ fontSize: '0.8rem', marginTop: 2 }}>
                      Passed syntax validation and import check. Ready to download.
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginBottom: 'var(--space-5)' }}>
                  {['notebook.ipynb', 'requirements.txt', 'README.md'].map((f) => (
                    <div key={f} style={{
                      display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
                      padding: 'var(--space-2) var(--space-3)',
                      background: 'var(--color-bg-input)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8rem',
                    }}>
                      <CheckCircle size={12} color="var(--color-accent-success)" />
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{f}</span>
                    </div>
                  ))}
                </div>

                <button
                  id="download-bundle-btn"
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  <Download size={16} /> Download ZIP Bundle
                </button>
                <button
                  className="btn btn-secondary mt-4"
                  style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--space-2)' }}
                  onClick={() => setGenerated(false)}
                >
                  Regenerate
                </button>
              </>
            )}
          </div>

          {/* Validation checklist */}
          <div className="card">
            <div className="card-title mb-4">Validation Checklist</div>
            {[
              { label: 'AST Syntax Check', done: generated },
              { label: 'Import Completeness', done: generated },
              { label: 'Notebook Schema Valid', done: generated },
              { label: 'ZIP Bundle Integrity', done: generated },
            ].map((item) => (
              <div key={item.label} style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                padding: 'var(--space-2) 0',
                borderBottom: '1px solid var(--color-border)',
                fontSize: '0.85rem',
              }}>
                {item.done
                  ? <CheckCircle size={14} color="var(--color-accent-success)" />
                  : <AlertCircle size={14} color="var(--color-text-muted)" />}
                <span style={{ color: item.done ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
