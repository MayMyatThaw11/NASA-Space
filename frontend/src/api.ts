import type { Incident, Result, YearAnalysis } from './types';
import type { Language } from './i18n';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const pendingTts = new Map<string, Promise<Blob>>();
const ttsControllers = new Set<AbortController>();
let unavailableUntil = 0;
let unavailableMessage = '';

export function cancelTts() { ttsControllers.forEach((controller) => controller.abort()); ttsControllers.clear(); }

export function tts(text: string, language: Language, signal?: AbortSignal) {
  if (Date.now() < unavailableUntil) return Promise.reject(new Error(unavailableMessage));
  const key = `${language}:${text}`;
  const existing = pendingTts.get(key);
  if (existing) return existing;
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort();
  if (signal?.aborted) return Promise.reject(new DOMException('The request was aborted.', 'AbortError'));
  signal?.addEventListener('abort', abortFromCaller, { once: true });
  ttsControllers.add(controller);
  const request = (async () => {
    const response = await fetch(`${API}/api/tts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, language }), signal: controller.signal });
    if (!response.ok) {
      let detail = 'TTS unavailable';
      try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail; } catch { /* keep sanitized fallback */ }
      if (response.status === 503 && /location|region|provider/i.test(detail)) { unavailableMessage = detail; unavailableUntil = Date.now() + 60000; }
      throw new Error(detail);
    }
    return response.blob();
  })().finally(() => { pendingTts.delete(key); ttsControllers.delete(controller); signal?.removeEventListener('abort', abortFromCaller); });
  pendingTts.set(key, request);
  return request;
}

export async function explain(result: Result, language: Language, signal?: AbortSignal) {
  const response = await fetch(`${API}/api/explanation`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ result, language }), signal });
  if (!response.ok) throw new Error('Explanation unavailable');
  return response.json() as Promise<{ text?: string; fallback?: boolean; reason?: string }>;
}

export async function localUpdates(region: string, township?: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ region });
  if (township) params.set('township', township);
  const response = await fetch(`${API}/api/local-updates?${params.toString()}`, { signal });
  if (!response.ok) throw new Error('Local updates unavailable');
  return response.json() as Promise<{ incidents: Incident[]; available: boolean }>;
}

export async function yearData(year: number, region: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ year: String(year), region });
  const response = await fetch(`${API}/api/year-data?${params.toString()}`, { signal });
  if (!response.ok) throw new Error('Year data unavailable');
  return response.json() as Promise<YearAnalysis>;
}
