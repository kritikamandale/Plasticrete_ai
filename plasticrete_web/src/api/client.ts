import type {
  MixInput,
  PredictionResponse,
  ScoreResponse,
  RecommendationResponse,
  OptimizeRequest,
  OptimizeResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const DEFAULT_MIX: MixInput = {
  plastic_type: 'PET',
  replacement_pct: 15.0,
  particle_size_mm: 4.0,
  wc_ratio: 0.45,
  additive_type: 'fly_ash',
  additive_pct: 10.0,
  curing_temp_c: 27.0,
  curing_days: 28,
};

async function readError(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  return `${fallback} (HTTP ${res.status}).`;
}

function requireMean(pred: PredictionResponse, key: string): number {
  const value = pred.predictions[key]?.mean;
  if (value == null || Number.isNaN(Number(value))) {
    throw new Error(`M1 did not return ${key}.`);
  }
  return Number(value);
}

function confidenceBounds(pred: PredictionResponse) {
  const ci_90_low: Record<string, number> = {};
  const ci_90_high: Record<string, number> = {};
  for (const [key, value] of Object.entries(pred.predictions)) {
    if (value?.ci_90_low != null) ci_90_low[key] = value.ci_90_low;
    if (value?.ci_90_high != null) ci_90_high[key] = value.ci_90_high;
  }
  return { ci_90_low, ci_90_high };
}

function propertyPayload(mix: MixInput, pred: PredictionResponse) {
  return {
    ...mix,
    compressive_strength_mpa: requireMean(pred, 'compressive_strength_mpa'),
    flexural_strength_mpa: requireMean(pred, 'flexural_strength_mpa'),
    split_tensile_mpa: requireMean(pred, 'split_tensile_mpa'),
    density_kgm3: requireMean(pred, 'density_kgm3'),
    water_absorption_pct: requireMean(pred, 'water_absorption_pct'),
    thermal_conductivity_wm: requireMean(pred, 'thermal_conductivity_wm'),
    durability_index: requireMean(pred, 'durability_index'),
    ...confidenceBounds(pred),
  };
}

export async function predictProperties(mix: MixInput): Promise<PredictionResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mix),
  });
  if (!res.ok) throw new Error(await readError(res, 'Property prediction failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function scoreSustainability(mix: MixInput, pred: PredictionResponse): Promise<ScoreResponse> {
  const res = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(propertyPayload(mix, pred)),
  });
  if (!res.ok) throw new Error(await readError(res, 'Sustainability score failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function recommendApplications(mix: MixInput, pred: PredictionResponse): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(propertyPayload(mix, pred)),
  });
  if (!res.ok) throw new Error(await readError(res, 'Product recommendation failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function runOptimization(req: OptimizeRequest): Promise<OptimizeResponse> {
  const res = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(await readError(res, 'The mix search failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function generateReport(
  mix: MixInput,
  prediction: PredictionResponse,
  score: ScoreResponse,
  recommendation: RecommendationResponse,
  sessionId?: string,
  batchId?: string,
): Promise<boolean> {
  const payload = {
    mix_params: mix,
    prediction,
    score,
    recommendation,
    session_id: sessionId || `PLT-${new Date().toISOString().slice(0, 10)}`,
    batch_id: batchId,
  };
  const res = await fetch(`${API_BASE}/report/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readError(res, 'PDF generation failed'));
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `plasticrete_report_${sessionId || 'mix'}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return true;
}

export interface SavedBatch {
  id: string;
  plant_name: string;
  created_at: string;
  cast_date: string | null;
  mix_params: MixInput;
  prediction: PredictionResponse;
  score: ScoreResponse;
  recommendation: RecommendationResponse;
  predicted_cs_mean: number | null;
  predicted_cs_low: number | null;
  predicted_cs_high: number | null;
  measured_cs_7d: number | null;
  measured_cs_28d: number | null;
  measured_absorption_pct: number | null;
  error_mpa: number | null;
  model_version: string;
  qr_url: string;
  notes: string | null;
  calibration: {
    ready: boolean;
    n_pairs: number;
    mean_error_mpa: number | null;
    residual_std_mpa: number | null;
    message: string;
  };
}

export async function createBatch(input: {
  plant_name: string;
  cast_date?: string;
  mix_params: MixInput;
  prediction: PredictionResponse;
  score: ScoreResponse;
  recommendation: RecommendationResponse;
}): Promise<SavedBatch> {
  const res = await fetch(`${API_BASE}/batches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(await readError(res, 'Could not save the batch'));
  return res.json();
}

export async function fetchBatch(id: string): Promise<SavedBatch> {
  const res = await fetch(`${API_BASE}/batches/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(res.status === 404 ? 'Batch not found.' : await readError(res, 'Could not load the batch'));
  return res.json();
}

export async function updateBatch(id: string, body: {
  cast_date?: string;
  measured_cs_7d?: number;
  measured_cs_28d?: number;
  measured_absorption_pct?: number;
  notes?: string;
}): Promise<SavedBatch> {
  const res = await fetch(`${API_BASE}/batches/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await readError(res, 'Could not save the lab result'));
  return res.json();
}

export async function uploadBatchPhoto(id: string, file: File): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/batches/${encodeURIComponent(id)}/photo`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(await readError(res, 'Photo upload failed'));
}

export function batchPhotoUrl(id: string): string {
  return `${API_BASE}/batches/${encodeURIComponent(id)}/photo`;
}
