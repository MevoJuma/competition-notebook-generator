import { useEffect, useRef, useState, useCallback } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export type PipelineStage = {
  stage: number;
  name: string;
  status: 'idle' | 'running' | 'done' | 'error';
  data?: Record<string, unknown>;
};

export type SSEStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

export type PipelineResult = {
  problem_type?: string;
  target?: string;
  metric?: string;
  cv_strategy?: string;
  leakage?: boolean;
};

const STAGE_NAMES = [
  'Document Analysis',
  'Data Profiling',
  'Schema Reconciliation',
  'Task Classification',
  'Validation Engine',
];

function initStages(): PipelineStage[] {
  return STAGE_NAMES.map((name, i) => ({
    stage: i + 1,
    name,
    status: 'idle',
  }));
}

/**
 * Connects to the backend SSE stream for a given competition and tracks pipeline stages.
 * Returns the current stages, connection status, final result, and a start/stop control.
 */
export function usePipelineSSE(competitionId: string | null) {
  const [stages, setStages] = useState<PipelineStage[]>(initStages());
  const [sseStatus, setSseStatus] = useState<SSEStatus>('idle');
  const [result, setResult] = useState<PipelineResult | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const disconnect = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setSseStatus('closed');
  }, []);

  const connect = useCallback(() => {
    if (!competitionId) return;
    if (esRef.current) disconnect();

    setStages(initStages());
    setResult(null);
    setSseStatus('connecting');

    const url = `${BASE_URL}/api/v1/events/${competitionId}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => setSseStatus('open');
    es.onerror = () => { setSseStatus('error'); es.close(); };

    es.addEventListener('connected', () => setSseStatus('open'));
    es.addEventListener('heartbeat', () => {});

    es.addEventListener('stage_start', (e) => {
      const d = JSON.parse(e.data) as { stage: number; name: string };
      setStages((prev) =>
        prev.map((s) => s.stage === d.stage ? { ...s, status: 'running' } : s)
      );
    });

    es.addEventListener('stage_done', (e) => {
      const d = JSON.parse(e.data) as { stage: number; name: string } & Record<string, unknown>;
      setStages((prev) =>
        prev.map((s) => s.stage === d.stage ? { ...s, status: 'done', data: d } : s)
      );
    });

    es.addEventListener('completed', (e) => {
      const d = JSON.parse(e.data) as PipelineResult;
      setResult(d);
      setSseStatus('closed');
      es.close();
    });

    es.addEventListener('failed', (e) => {
      const d = JSON.parse(e.data) as { error: string };
      console.error('Pipeline failed:', d.error);
      setStages((prev) => prev.map((s) => s.status === 'running' ? { ...s, status: 'error' } : s));
      setSseStatus('error');
      es.close();
    });
  }, [competitionId, disconnect]);

  // Auto-cleanup on unmount
  useEffect(() => () => { esRef.current?.close(); }, []);

  return { stages, sseStatus, result, connect, disconnect };
}
