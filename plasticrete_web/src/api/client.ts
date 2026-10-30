import type {
  MixInput,
  PredictionResponse,
  ScoreResponse,
  RecommendationResponse,
  OptimizeRequest,
  OptimizeResponse,
  FormulationRecord,
  FormulationCreatePayload,
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

// Configurable timeouts per workload category
export const TIMEOUTS = {
  PREDICT_MS: 25000,     // M1 ensemble prediction with SHAP (up to 25s)
  SCORE_MS: 15000,       // M3 sustainability scoring (15s)
  RECOMMEND_MS: 15000,   // M4 application classification & FAISS retrieval (15s)
  OPTIMIZE_MS: 120000,   // M2 Optuna 80-trial search (this machine often needs >35s)
  REPORT_PDF_MS: 25000,  // PDF Report generation (25s)
  BATCH_MS: 15000,       // Batch CRUD & photo upload (15s)
};

async function readError(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => ({}));
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  return `${fallback} (HTTP ${res.status}).`;
}

/**
 * Robust fetch wrapper with configurable abort timeout and error normalization
 */
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 25000): Promise<Response> {
  const timeoutController = new AbortController();
  const combined = new AbortController();
  const caller = options.signal;
  const timer = setTimeout(() => {
    timeoutController.abort(new DOMException(`Request timed out after ${timeoutMs / 1000} seconds`, 'TimeoutError'));
  }, timeoutMs);

  const abortCombined = () => {
    if (!combined.signal.aborted) combined.abort();
  };
  timeoutController.signal.addEventListener('abort', abortCombined);
  caller?.addEventListener('abort', abortCombined);
  if (caller?.aborted || timeoutController.signal.aborted) abortCombined();

  try {
    return await fetch(url, { ...options, signal: combined.signal });
  } catch (err: unknown) {
    if (caller?.aborted) throw err;
    if (timeoutController.signal.aborted) {
      throw new Error(`The operation timed out after ${timeoutMs / 1000}s. The server may still be processing.`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
    timeoutController.signal.removeEventListener('abort', abortCombined);
    caller?.removeEventListener('abort', abortCombined);
  }
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

export async function predictProperties(mix: MixInput, signal?: AbortSignal): Promise<PredictionResponse> {
  const res = await fetchWithTimeout(
    `${API_BASE}/predict`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mix),
      signal,
    },
    TIMEOUTS.PREDICT_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Property prediction failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function scoreSustainability(
  mix: MixInput,
  pred: PredictionResponse,
  signal?: AbortSignal
): Promise<ScoreResponse> {
  const res = await fetchWithTimeout(
    `${API_BASE}/score`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(propertyPayload(mix, pred)),
      signal,
    },
    TIMEOUTS.SCORE_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Sustainability score failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function recommendApplications(
  mix: MixInput,
  pred: PredictionResponse,
  signal?: AbortSignal
): Promise<RecommendationResponse> {
  const res = await fetchWithTimeout(
    `${API_BASE}/recommend`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(propertyPayload(mix, pred)),
      signal,
    },
    TIMEOUTS.RECOMMEND_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Product recommendation failed'));
  const data = await res.json();
  return { ...data, source: 'live' };
}

export async function runOptimization(req: OptimizeRequest, signal?: AbortSignal): Promise<OptimizeResponse> {
  const res = await fetchWithTimeout(
    `${API_BASE}/optimize`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal,
    },
    TIMEOUTS.OPTIMIZE_MS
  );
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
  signal?: AbortSignal
): Promise<boolean> {
  const payload = {
    mix_params: mix,
    prediction,
    score,
    recommendation,
    session_id: sessionId || `PLT-${new Date().toISOString().slice(0, 10)}`,
    batch_id: batchId,
  };
  const res = await fetchWithTimeout(
    `${API_BASE}/report/pdf`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    },
    TIMEOUTS.REPORT_PDF_MS
  );
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
  due_7d?: string | null;
  due_28d?: string | null;
  cube_size_mm?: number | null;
  cube_photo_path?: string | null;
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
  const res = await fetchWithTimeout(
    `${API_BASE}/batches`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Could not save the batch'));
  return res.json();
}

export interface BatchSummary {
  id: string;
  created_at: string;
  plant_name: string;
  plastic_type?: string;
  replacement_pct?: number;
  predicted_cs_mean: number | null;
  predicted_cs_low: number | null;
  predicted_cs_high: number | null;
  measured_cs_7d: number | null;
  measured_cs_28d: number | null;
  error_mpa?: number | null;
  notes?: string | null;
  has_photo?: boolean;
  cast_date: string | null;
  model_version: string;
}

export async function listBatches(limit = 50): Promise<BatchSummary[]> {
  const res = await fetchWithTimeout(`${API_BASE}/batches?limit=${limit}`, {}, TIMEOUTS.BATCH_MS);
  if (!res.ok) throw new Error(await readError(res, 'Could not load batch records'));
  return res.json();
}

export async function fetchBatch(id: string): Promise<SavedBatch> {
  const res = await fetchWithTimeout(`${API_BASE}/batches/${encodeURIComponent(id)}`, {}, TIMEOUTS.BATCH_MS);
  if (!res.ok) throw new Error(res.status === 404 ? 'Batch not found.' : await readError(res, 'Could not load the batch'));
  return res.json();
}

export async function updateBatch(id: string, body: {
  cast_date?: string;
  measured_cs_7d?: number;
  measured_cs_28d?: number;
  measured_absorption_pct?: number;
  notes?: string;
  lab_name?: string;
  operator?: string;
  cube_size_mm?: number;
  cube_values_mpa?: number[];
  test_standard?: string;
  confirm_high_cv?: boolean;
}): Promise<SavedBatch> {
  const res = await fetchWithTimeout(
    `${API_BASE}/batches/${encodeURIComponent(id)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Could not save the lab result'));
  return res.json();
}

export async function uploadBatchPhoto(id: string, file: File): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetchWithTimeout(
    `${API_BASE}/batches/${encodeURIComponent(id)}/photo`,
    {
      method: 'POST',
      body: form,
    },
    TIMEOUTS.BATCH_MS * 2
  );
  if (!res.ok) throw new Error(await readError(res, 'Photo upload failed'));
}

export async function deleteBatchPhoto(id: string): Promise<void> {
  const res = await fetchWithTimeout(
    `${API_BASE}/batches/${encodeURIComponent(id)}/photo`,
    { method: 'DELETE' },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Could not remove the photo'));
}

export async function scheduleVerification(input: {
  plant_name: string;
  cast_date?: string;
  mix_params: MixInput;
  prediction: PredictionResponse;
  score: ScoreResponse;
  recommendation: RecommendationResponse;
}): Promise<{ opened: boolean; batch: SavedBatch | null }> {
  const res = await fetchWithTimeout(
    `${API_BASE}/batches/schedule`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Could not open a verification passport'));
  return res.json();
}

export async function fetchDueBatches(): Promise<{ id: string }[]> {
  const res = await fetchWithTimeout(`${API_BASE}/batches/due`, {}, TIMEOUTS.BATCH_MS);
  if (!res.ok) throw new Error(await readError(res, 'Could not load due batches'));
  return res.json();
}

export function batchPhotoUrl(id: string): string {
  return `${API_BASE}/batches/${encodeURIComponent(id)}/photo`;
}


// ═══════════════════════════════════════════════════════════
// Formulations Database Persistence Client
// ═══════════════════════════════════════════════════════════

export async function listSavedFormulations(search?: string, limit = 50): Promise<FormulationRecord[]> {
  const q = new URLSearchParams();
  if (search) q.set('search', search);
  q.set('limit', String(limit));
  const res = await fetchWithTimeout(`${API_BASE}/formulations?${q.toString()}`, {}, TIMEOUTS.BATCH_MS);
  if (!res.ok) throw new Error(await readError(res, 'Could not retrieve formulations'));
  return res.json();
}

export async function getSavedFormulation(id: string): Promise<FormulationRecord> {
  const res = await fetchWithTimeout(`${API_BASE}/formulations/${encodeURIComponent(id)}`, {}, TIMEOUTS.BATCH_MS);
  if (!res.ok) throw new Error(await readError(res, 'Could not load formulation'));
  return res.json();
}

export async function saveFormulation(payload: FormulationCreatePayload): Promise<FormulationRecord> {
  const res = await fetchWithTimeout(
    `${API_BASE}/formulations`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Failed to save formulation'));
  return res.json();
}

export async function updateSavedFormulation(
  id: string,
  payload: Partial<FormulationCreatePayload>
): Promise<FormulationRecord> {
  const res = await fetchWithTimeout(
    `${API_BASE}/formulations/${encodeURIComponent(id)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Failed to update formulation'));
  return res.json();
}

export async function duplicateSavedFormulation(id: string, newName?: string): Promise<FormulationRecord> {
  const q = newName ? `?name=${encodeURIComponent(newName)}` : '';
  const res = await fetchWithTimeout(
    `${API_BASE}/formulations/${encodeURIComponent(id)}/duplicate${q}`,
    {
      method: 'POST',
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Failed to duplicate formulation'));
  return res.json();
}

export async function deleteSavedFormulation(id: string): Promise<{ deleted: boolean; id: string }> {
  const res = await fetchWithTimeout(
    `${API_BASE}/formulations/${encodeURIComponent(id)}`,
    {
      method: 'DELETE',
    },
    TIMEOUTS.BATCH_MS
  );
  if (!res.ok) throw new Error(await readError(res, 'Failed to delete formulation'));
  return res.json();
}
