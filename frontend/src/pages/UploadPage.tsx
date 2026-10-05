import { useState, useCallback, useRef } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, FolderOpen, Play } from 'lucide-react';
import { competitionsApi, filesApi } from '../api/client';
import { usePipelineSSE } from '../hooks/usePipelineSSE';

interface QueuedFile {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'done' | 'error';
  progress: number;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileCategory(name: string): { label: string; color: string } {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  if (['csv', 'parquet'].includes(ext)) return { label: 'Dataset', color: 'badge-green' };
  if (['pdf', 'docx', 'txt'].includes(ext)) return { label: 'Document', color: 'badge-cyan' };
  if (['zip', 'tar', 'gz'].includes(ext)) return { label: 'Archive', color: 'badge-yellow' };
  return { label: 'Other', color: 'badge-purple' };
}

const STAGE_STATUS_COLOR: Record<string, string> = {
  idle: 'var(--color-text-muted)',
  running: 'var(--color-accent-primary)',
  done: 'var(--color-accent-success)',
  error: 'var(--color-accent-danger)',
};

export default function UploadPage() {
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [competitionName, setCompetitionName] = useState('');
  const [platform, setPlatform] = useState('zindi');
  const [competitionId, setCompetitionId] = useState<string | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { stages, sseStatus, result, connect } = usePipelineSSE(competitionId);

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    const newFiles: QueuedFile[] = Array.from(incoming).map((f) => ({
      id: `${f.name}-${Date.now()}`,
      file: f,
      status: 'pending',
      progress: 0,
    }));
    setQueuedFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = (id: string) =>
    setQueuedFiles((prev) => prev.filter((f) => f.id !== id));

  const handleAnalyse = async () => {
    if (!competitionName.trim() || queuedFiles.length === 0) return;
    setGlobalError(null);
    setIsRunning(true);

    try {
      // 1. Create competition
      const { data: comp } = await competitionsApi.create(competitionName, platform);
      setCompetitionId(comp.id);

      // 2. Upload each file sequentially
      for (const qf of queuedFiles) {
        setQueuedFiles((prev) =>
          prev.map((f) => f.id === qf.id ? { ...f, status: 'uploading' } : f)
        );
        await filesApi.upload(comp.id, qf.file, (pct) => {
          setQueuedFiles((prev) =>
            prev.map((f) => f.id === qf.id ? { ...f, progress: pct } : f)
          );
        });
        setQueuedFiles((prev) =>
          prev.map((f) => f.id === qf.id ? { ...f, status: 'done', progress: 100 } : f)
        );
      }

      // 3. Start SSE stream (pipeline is triggered server-side after upload)
      connect();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setGlobalError(msg);
      setIsRunning(false);
    }
  };

  const pipelineStarted = sseStatus !== 'idle';

  return (
    <div className="page animate-fade-in">
      <div className="grid-2" style={{ alignItems: 'start', gap: 'var(--space-6)' }}>
        {/* Left: drop zone + file list */}
        <div>
          <div
            id="upload-dropzone"
            className={`upload-zone mb-6 ${dragOver ? 'drag-over' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
          >
            <input
              ref={inputRef}
              id="file-input"
              type="file"
              multiple
              style={{ display: 'none' }}
              accept=".csv,.parquet,.pdf,.docx,.txt,.zip"
              onChange={(e) => addFiles(e.target.files)}
            />
            <div className="upload-icon">
              <Upload size={24} color="var(--color-text-accent)" />
            </div>
            <div className="upload-title">Drop files here or click to browse</div>
            <div className="upload-hint" style={{ marginTop: 'var(--space-2)' }}>
              Supports CSV, Parquet, PDF, DOCX, TXT, ZIP
            </div>
          </div>

          {queuedFiles.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <FolderOpen size={16} style={{ display: 'inline', marginRight: 6 }} />
                  Queued Files ({queuedFiles.length})
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => setQueuedFiles([])}>
                  Clear all
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {queuedFiles.map((qf) => {
                  const cat = fileCategory(qf.file.name);
                  return (
                    <div key={qf.id} style={{
                      padding: 'var(--space-3)',
                      background: 'var(--color-bg-input)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                        <File size={16} color="var(--color-text-muted)" />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: '0.85rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {qf.file.name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            {formatBytes(qf.file.size)}
                          </div>
                        </div>
                        <span className={`badge ${cat.color}`}>{cat.label}</span>
                        {qf.status === 'uploading' && <div className="spinner" style={{ width: 14, height: 14 }} />}
                        {qf.status === 'done' && <CheckCircle size={16} color="var(--color-accent-success)" />}
                        {qf.status === 'error' && <AlertCircle size={16} color="var(--color-accent-danger)" />}
                        {qf.status === 'pending' && (
                          <button className="btn-icon" style={{ width: 28, height: 28 }} onClick={() => removeFile(qf.id)}>
                            <X size={12} />
                          </button>
                        )}
                      </div>
                      {qf.status === 'uploading' && (
                        <div className="progress-bar" style={{ marginTop: 'var(--space-2)' }}>
                          <div className="progress-fill" style={{ width: `${qf.progress}%` }} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Pipeline status (shown once SSE starts) */}
          {pipelineStarted && (
            <div className="card mt-4" style={{ marginTop: 'var(--space-4)' }}>
              <div className="card-header mb-4">
                <div className="card-title">Live Pipeline</div>
                <span className={`badge ${sseStatus === 'open' ? 'badge-green' : sseStatus === 'error' ? 'badge-red' : 'badge-yellow'}`}>
                  {sseStatus}
                </span>
              </div>
              <div className="pipeline">
                {stages.map((s) => (
                  <div key={s.stage} className={`pipeline-step ${s.status === 'done' ? 'done' : s.status === 'running' ? 'active' : ''}`}>
                    <div className="pipeline-step-number" style={{ color: STAGE_STATUS_COLOR[s.status] }}>
                      {s.status === 'done' ? '✓' : s.stage}
                    </div>
                    <div className="pipeline-step-content">
                      <div className="pipeline-step-title">{s.name}</div>
                      {s.data && (
                        <div className="pipeline-step-desc">
                          {Object.entries(s.data)
                            .filter(([k]) => !['stage', 'name'].includes(k))
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(' · ')}
                        </div>
                      )}
                    </div>
                    {s.status === 'running' && <div className="spinner" />}
                  </div>
                ))}
              </div>

              {result && (
                <div className="alert alert-success" style={{ marginTop: 'var(--space-4)' }}>
                  <CheckCircle size={16} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Analysis complete!</strong>
                    <div style={{ fontSize: '0.8rem', marginTop: 4 }}>
                      {result.problem_type} · Target: {result.target} · Metric: {result.metric} · CV: {result.cv_strategy}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Competition metadata form */}
        <div className="card animate-fade-in-1">
          <div className="card-header mb-4">
            <div>
              <div className="card-title">Competition Details</div>
              <div className="card-subtitle">Provide context to improve AI analysis</div>
            </div>
          </div>

          {globalError && (
            <div className="alert alert-danger mb-4">
              <AlertCircle size={14} style={{ flexShrink: 0 }} />
              {globalError}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="comp-name">Competition Name</label>
            <input
              id="comp-name"
              className="form-input"
              placeholder="e.g. Financial Inclusion in Africa"
              value={competitionName}
              onChange={(e) => setCompetitionName(e.target.value)}
              disabled={isRunning}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="comp-platform">Platform</label>
            <select
              id="comp-platform"
              className="form-select"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              disabled={isRunning}
            >
              <option value="zindi">Zindi</option>
              <option value="kaggle">Kaggle</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="divider" />

          <div className="alert alert-info mb-4">
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              Upload at least <strong>train.csv</strong> and optionally <strong>test.csv</strong>,
              a sample submission CSV, and any PDF/DOCX competition rules.
            </div>
          </div>

          <button
            id="start-analysis-btn"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={queuedFiles.length === 0 || !competitionName.trim() || isRunning}
            onClick={handleAnalyse}
          >
            {isRunning
              ? <><div className="spinner" /> Running…</>
              : <><Play size={16} /> Analyse {queuedFiles.length} file{queuedFiles.length !== 1 ? 's' : ''}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
