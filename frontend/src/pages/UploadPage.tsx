import { useState, useCallback, useRef } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, FolderOpen } from 'lucide-react';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'done' | 'error';
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

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [competitionName, setCompetitionName] = useState('');
  const [competitionUrl, setCompetitionUrl] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    const newFiles: UploadedFile[] = Array.from(incoming).map((f) => ({
      id: `${f.name}-${Date.now()}`,
      name: f.name,
      size: f.size,
      type: f.type,
      status: 'pending',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id));

  const simulateUpload = () => {
    setFiles((prev) => prev.map((f) => ({ ...f, status: 'uploading' as const })));
    setTimeout(() => {
      setFiles((prev) => prev.map((f) => ({ ...f, status: 'done' as const })));
    }, 1500);
  };

  return (
    <div className="page animate-fade-in">
      <div className="grid-2" style={{ alignItems: 'start', gap: 'var(--space-6)' }}>
        {/* Left: Upload zone + file list */}
        <div>
          {/* Drop zone */}
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

          {/* File list */}
          {files.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <FolderOpen size={16} style={{ display: 'inline', marginRight: 6 }} />
                  Queued Files ({files.length})
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => setFiles([])}>Clear all</button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {files.map((f) => {
                  const cat = fileCategory(f.name);
                  return (
                    <div key={f.id} style={{
                      display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                      padding: 'var(--space-3)',
                      background: 'var(--color-bg-input)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                    }}>
                      <File size={16} color="var(--color-text-muted)" />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '0.85rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {f.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{formatBytes(f.size)}</div>
                      </div>
                      <span className={`badge ${cat.color}`}>{cat.label}</span>
                      {f.status === 'uploading' && <div className="spinner" style={{ width: 14, height: 14 }} />}
                      {f.status === 'done' && <CheckCircle size={16} color="var(--color-accent-success)" />}
                      {f.status === 'error' && <AlertCircle size={16} color="var(--color-accent-danger)" />}
                      {f.status === 'pending' && (
                        <button id={`remove-${f.id}`} className="btn-icon" style={{ width: 28, height: 28 }} onClick={() => removeFile(f.id)}>
                          <X size={12} />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
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

          <div className="form-group">
            <label className="form-label" htmlFor="comp-name">Competition Name</label>
            <input
              id="comp-name"
              className="form-input"
              placeholder="e.g. Financial Inclusion in Africa"
              value={competitionName}
              onChange={(e) => setCompetitionName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="comp-url">Competition URL (optional)</label>
            <input
              id="comp-url"
              className="form-input"
              placeholder="https://zindi.africa/competitions/..."
              value={competitionUrl}
              onChange={(e) => setCompetitionUrl(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="comp-platform">Platform</label>
            <select id="comp-platform" className="form-select">
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
            disabled={files.length === 0}
            onClick={simulateUpload}
          >
            <Upload size={16} />
            {files.length === 0 ? 'Add files to begin' : `Analyse ${files.length} file${files.length > 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
