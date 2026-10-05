import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ── Types ──────────────────────────────────────────────────────────────────
export interface Competition {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

export interface UploadedFile {
  id: string;
  filename: string;
  file_size: number;
  file_type: string;
  role: string;
}

// ── Competitions ───────────────────────────────────────────────────────────
export const competitionsApi = {
  list: () => api.get<Competition[]>('/competitions'),

  create: (name: string, platform = 'zindi') =>
    api.post<Competition>('/competitions', { name, platform }),

  get: (id: string) => api.get<Competition>(`/competitions/${id}`),

  delete: (id: string) => api.delete(`/competitions/${id}`),
};

// ── Files ──────────────────────────────────────────────────────────────────
export const filesApi = {
  upload: (competitionId: string, file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append('file', file);
    return api.post<UploadedFile>(`/files/${competitionId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    });
  },

  list: (competitionId: string) =>
    api.get<UploadedFile[]>(`/files/${competitionId}`),
};

// ── Notebook ───────────────────────────────────────────────────────────────
export const notebookApi = {
  generate: async (plan: object): Promise<Blob> => {
    const resp = await api.post('/notebooks/generate', plan, { responseType: 'blob' });
    return resp.data as Blob;
  },

  download: (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
