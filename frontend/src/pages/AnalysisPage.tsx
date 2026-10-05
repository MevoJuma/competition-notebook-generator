import { Target, BarChart3, ShieldAlert, GitBranch, TrendingUp } from 'lucide-react';

const MOCK_PROFILE = {
  competitionTitle: 'Financial Inclusion in Africa',
  problemType: 'Binary Classification',
  targetColumn: 'bank_account',
  idColumn: 'uniqueid',
  metric: 'ROC-AUC',
  confidence: 0.92,
  cvStrategy: 'StratifiedKFold',
  trainRows: 23524,
  testRows: 15139,
  features: 23,
  leakage: false,
};

const MOCK_COLUMNS = [
  { name: 'uniqueid', dtype: 'String', nulls: 0, unique: 23524, role: 'ID' },
  { name: 'bank_account', dtype: 'Int64', nulls: 0, unique: 2, role: 'Target' },
  { name: 'country', dtype: 'String', nulls: 0, unique: 4, role: 'Feature' },
  { name: 'year', dtype: 'Int64', nulls: 0, unique: 3, role: 'Feature' },
  { name: 'location_type', dtype: 'String', nulls: 0, unique: 2, role: 'Feature' },
  { name: 'cellphone_access', dtype: 'String', nulls: 0, unique: 2, role: 'Feature' },
  { name: 'household_size', dtype: 'Float64', nulls: 12, unique: 21, role: 'Feature' },
  { name: 'age_of_respondent', dtype: 'Int64', nulls: 0, unique: 67, role: 'Feature' },
];

const MOCK_IMPORTANCES = [
  { feature: 'age_of_respondent', importance: 0.241 },
  { feature: 'household_size', importance: 0.198 },
  { feature: 'cellphone_access', importance: 0.164 },
  { feature: 'country', importance: 0.142 },
  { feature: 'location_type', importance: 0.117 },
  { feature: 'year', importance: 0.083 },
];

function RoleTag({ role }: { role: string }) {
  const map: Record<string, string> = { ID: 'badge-cyan', Target: 'badge-green', Feature: 'badge-purple' };
  return <span className={`badge ${map[role] ?? 'badge-purple'}`}>{role}</span>;
}

export default function AnalysisPage() {
  return (
    <div className="page animate-fade-in">
      {/* Summary cards */}
      <div className="grid-4 mb-6 animate-fade-in">
        {[
          { icon: <Target size={18} />, label: 'Problem Type', value: MOCK_PROFILE.problemType, color: 'var(--color-accent-primary)' },
          { icon: <BarChart3 size={18} />, label: 'Metric', value: MOCK_PROFILE.metric, color: 'var(--color-accent-tertiary)' },
          { icon: <GitBranch size={18} />, label: 'CV Strategy', value: MOCK_PROFILE.cvStrategy, color: 'var(--color-accent-secondary)' },
          { icon: <TrendingUp size={18} />, label: 'Confidence', value: `${(MOCK_PROFILE.confidence * 100).toFixed(0)}%`, color: 'var(--color-accent-success)' },
        ].map((c) => (
          <div key={c.label} className="card">
            <div style={{ color: c.color, marginBottom: 'var(--space-3)' }}>{c.icon}</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: 2 }}>{c.value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>{c.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2 animate-fade-in-1" style={{ gap: 'var(--space-5)', alignItems: 'start' }}>
        {/* Column profiles */}
        <div className="card">
          <div className="card-header mb-4">
            <div className="card-title">Column Profiles</div>
            <span className="badge badge-cyan">{MOCK_COLUMNS.length} columns</span>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Nulls</th>
                  <th>Unique</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_COLUMNS.map((col) => (
                  <tr key={col.name}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{col.name}</td>
                    <td><span className="badge badge-purple">{col.dtype}</span></td>
                    <td style={{ color: col.nulls > 0 ? 'var(--color-accent-warning)' : 'var(--color-text-muted)' }}>
                      {col.nulls}
                    </td>
                    <td>{col.unique.toLocaleString()}</td>
                    <td><RoleTag role={col.role} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Leakage status */}
          <div className={`alert ${MOCK_PROFILE.leakage ? 'alert-danger' : 'alert-success'}`}>
            <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <strong>{MOCK_PROFILE.leakage ? '⚠ Leakage Detected' : '✓ No Leakage Detected'}</strong>
              <div style={{ fontSize: '0.8rem', marginTop: 2 }}>
                {MOCK_PROFILE.leakage
                  ? 'Target column found in test set or ID ranges overlap.'
                  : 'Train/test splits are clean. Target absent from test schema.'}
              </div>
            </div>
          </div>

          {/* Dataset sizes */}
          <div className="card">
            <div className="card-title mb-4">Dataset Overview</div>
            {[
              { label: 'Train rows', value: MOCK_PROFILE.trainRows.toLocaleString(), pct: 60 },
              { label: 'Test rows', value: MOCK_PROFILE.testRows.toLocaleString(), pct: 40 },
              { label: 'Features', value: String(MOCK_PROFILE.features), pct: 75 },
            ].map((item) => (
              <div key={item.label} style={{ marginBottom: 'var(--space-4)' }}>
                <div className="flex justify-between mb-4" style={{ marginBottom: 'var(--space-2)' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{item.label}</span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{item.value}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>

          {/* Feature importances */}
          <div className="card">
            <div className="card-title mb-4">LightGBM Feature Importance</div>
            {MOCK_IMPORTANCES.map((fi) => (
              <div key={fi.feature} style={{ marginBottom: 'var(--space-3)' }}>
                <div className="flex justify-between" style={{ marginBottom: 'var(--space-1)' }}>
                  <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>{fi.feature}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {(fi.importance * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${fi.importance * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
