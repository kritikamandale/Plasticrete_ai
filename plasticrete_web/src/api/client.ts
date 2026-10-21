import type {
  MixInput,
  PredictionResponse,
  ScoreResponse,
  RecommendationResponse,
  OptimizeRequest,
  OptimizeResponse,
  TradeoffPoint,
} from '../types';
import { computeMassBalance } from '../lib/massBalance';
import { evaluateUseClasses, statusForApplication } from '../lib/useClassGate';

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

// ── Realistic Offline Fallbacks ────────────────────────────────────────────────
function generateMockPrediction(mix: MixInput): PredictionResponse {
  const repFactor = 1.0 - (mix.replacement_pct / 100) * 0.8;
  const additiveBonus = mix.additive_type !== 'none' ? 1.0 + (mix.additive_pct / 100) * 0.6 : 1.0;
  const curingBonus = Math.min(1.3, 0.7 + Math.log10(mix.curing_days) * 0.35);

  const baseCS = 38.5 * repFactor * additiveBonus * curingBonus * (0.5 / mix.wc_ratio);
  const cs = Math.max(10.0, Math.min(65.0, baseCS));
  const flexural = cs * 0.16 + 0.5;
  const splitTensile = cs * 0.09 + 0.3;
  const density = 2400 - mix.replacement_pct * 12.5;
  const waterAbs = 2.5 + mix.replacement_pct * 0.18 * (mix.wc_ratio / 0.45);
  const thermalCond = 1.5 - mix.replacement_pct * 0.022;
  const durability = Math.min(95, Math.max(40, 75 - mix.replacement_pct * 0.6 + mix.additive_pct * 0.5));

  return {
    predictions: {
      compressive_strength_mpa: {
        mean: Math.round(cs * 10) / 10,
        ci_90_low: Math.round((cs - 2.2) * 10) / 10,
        ci_90_high: Math.round((cs + 2.5) * 10) / 10,
      },
      flexural_strength_mpa: {
        mean: Math.round(flexural * 10) / 10,
        ci_90_low: Math.round((flexural - 0.4) * 10) / 10,
        ci_90_high: Math.round((flexural + 0.4) * 10) / 10,
      },
      split_tensile_mpa: {
        mean: Math.round(splitTensile * 10) / 10,
        ci_90_low: Math.round((splitTensile - 0.3) * 10) / 10,
        ci_90_high: Math.round((splitTensile + 0.3) * 10) / 10,
      },
      density_kgm3: {
        mean: Math.round(density),
        ci_90_low: Math.round(density - 35),
        ci_90_high: Math.round(density + 40),
      },
      water_absorption_pct: {
        mean: Math.round(waterAbs * 10) / 10,
        ci_90_low: Math.round((waterAbs - 0.5) * 10) / 10,
        ci_90_high: Math.round((waterAbs + 0.6) * 10) / 10,
      },
      thermal_conductivity_wm: {
        mean: Math.round(thermalCond * 100) / 100,
        ci_90_low: Math.round((thermalCond - 0.08) * 100) / 100,
        ci_90_high: Math.round((thermalCond + 0.09) * 100) / 100,
      },
      durability_index: {
        mean: Math.round(durability),
        ci_90_low: Math.round(durability - 5),
        ci_90_high: Math.round(durability + 5),
      },
    },
    shap_values: {
      compressive_strength_mpa: {
        [`replacement_pct=${mix.replacement_pct}%`]: -((mix.replacement_pct * 0.25).toFixed(1) as unknown as number),
        [`wc_ratio=${mix.wc_ratio}`]: mix.wc_ratio <= 0.45 ? 2.4 : -2.8,
        [`additive=${mix.additive_type}`]: mix.additive_type !== 'none' ? 3.1 : -1.2,
        [`curing_days=${mix.curing_days}d`]: mix.curing_days >= 28 ? 3.5 : -1.8,
        [`particle_size=${mix.particle_size_mm}mm`]: -0.7,
      },
      durability_index: {
        [`additive_pct=${mix.additive_pct}%`]: 4.5,
        [`replacement_pct=${mix.replacement_pct}%`]: -3.2,
        [`curing_temp=${mix.curing_temp_c}°C`]: 1.2,
      },
    },
    uncertainty_flag: mix.replacement_pct > 32 || mix.wc_ratio > 0.6,
    low_coverage_targets: mix.replacement_pct > 30 ? ['thermal_conductivity_wm'] : [],
    source: 'demo',
  };
}

function generateMockScore(mix: MixInput, pred: PredictionResponse): ScoreResponse {
  const balance = computeMassBalance(mix);
  const mean = {
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.mean ?? null,
    water_absorption_pct: pred.predictions.water_absorption_pct?.mean ?? null,
    density_kgm3: pred.predictions.density_kgm3?.mean ?? null,
  };
  const low = {
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.ci_90_low ?? null,
    water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_low ?? null,
    density_kgm3: pred.predictions.density_kgm3?.ci_90_low ?? null,
  };
  const high = {
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.ci_90_high ?? null,
    water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_high ?? null,
    density_kgm3: pred.predictions.density_kgm3?.ci_90_high ?? null,
  };
  const useClassGates = evaluateUseClasses(mean, low, high);
  const allowed = useClassGates.filter((gate) => gate.status === 'allowed').length;
  const score = Math.round(Math.min(96, Math.max(20, 40 + balance.co2_saving_pct * 0.4 + allowed * 8)));
  const grade = score >= 85 ? 'A+' : score >= 75 ? 'A' : score >= 65 ? 'B' : 'C';

  return {
    sustainability_score: score,
    sustainability_grade: grade,
    embodied_carbon_kgco2e_m3: balance.co2_kgco2e_m3,
    co2_saving_pct: balance.co2_saving_pct,
    plastic_diversion_kg_m3: balance.plastic_kg_m3,
    pet_bottle_equiv: balance.pet_bottle_equiv,
    bis_overall_pass: useClassGates.some((gate) => gate.status === 'allowed'),
    igbc_total_credits: balance.plastic_kg_m3 >= 50 ? 2 : 0,
    griha_material_criterion_pts: balance.co2_saving_pct >= 10 ? 1 : 0,
    leed_total_points: mix.replacement_pct >= 10 ? 1 : 0,
    total_green_credits: (balance.plastic_kg_m3 >= 50 ? 2 : 0) + (balance.co2_saving_pct >= 10 ? 1 : 0) + (mix.replacement_pct >= 10 ? 1 : 0),
    top_negative_factor: mix.wc_ratio > 0.5 ? 'High water-binder ratio' : 'Strength loss from aggregate replacement',
    remediation_action_1: 'Lower the water/binder ratio before spending on a crush test.',
    remediation_action_2: 'Keep the SCM share inside the mass-balance recipe so the carbon number stays checkable.',
    remediation_action_3: 'Cast one verification batch when the 90% interval crosses the grade line.',
    estimated_score_gain: 0,
    mass_balance: balance,
    use_class_gates: useClassGates,
    source: 'demo',
  };
}

function generateMockRecommendation(mix: MixInput, pred: PredictionResponse): RecommendationResponse {
  const cs = pred.predictions.compressive_strength_mpa.mean || 25;
  let primary = 'paving_block_light';
  let confidence = 88.5;

  if (cs >= 30 && mix.replacement_pct <= 15) {
    primary = 'structural_concrete';
    confidence = 91.2;
  } else if (cs >= 25) {
    primary = 'paving_block_heavy';
    confidence = 89.0;
  } else if (cs >= 15) {
    primary = 'paving_block_light';
    confidence = 94.2;
  } else {
    primary = 'thermal_insulation_panel';
    confidence = 86.4;
  }

  const balance = computeMassBalance(mix);
  const classGates = evaluateUseClasses(
    {
      compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.mean ?? null,
      water_absorption_pct: pred.predictions.water_absorption_pct?.mean ?? null,
      density_kgm3: pred.predictions.density_kgm3?.mean ?? null,
    },
    {
      compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.ci_90_low ?? null,
      water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_low ?? null,
      density_kgm3: pred.predictions.density_kgm3?.ci_90_low ?? null,
    },
    {
      compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.ci_90_high ?? null,
      water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_high ?? null,
      density_kgm3: pred.predictions.density_kgm3?.ci_90_high ?? null,
    },
  );
  let gate = statusForApplication(primary, classGates);
  if (gate.status !== 'allowed' && gate.status !== 'lab_trial') {
    const fallback = classGates.find((item) => item.status === 'allowed' || item.status === 'lab_trial');
    if (fallback) {
      primary = fallback.applications[0];
      gate = statusForApplication(primary, classGates);
    }
  }
  const conventional = computeMassBalance({
    plastic_type: 'PET',
    replacement_pct: 0,
    wc_ratio: 0.5,
    additive_type: 'none',
    additive_pct: 0,
  });
  const saving = Number((conventional.cost_inr_m3 - balance.cost_inr_m3).toFixed(2));

  return {
    primary_application: primary,
    primary_confidence_pct: confidence,
    suitable_applications: [
      primary,
      'hollow_concrete_block',
      'plastic_sand_paver',
      'floor_tile_outdoor',
    ],
    suitability_scores: {
      [primary]: confidence,
      hollow_concrete_block: 76.4,
      plastic_sand_paver: 71.8,
      floor_tile_outdoor: 65.2,
      wall_cladding_panel: 58.0,
    },
    cost_benefit: {
      plastic_mix_cost_inr_m3: balance.cost_inr_m3,
      conventional_cost_inr_m3: conventional.cost_inr_m3,
      cost_saving_inr_m3: saving,
      cost_saving_pct: conventional.cost_inr_m3 ? Number(((saving / conventional.cost_inr_m3) * 100).toFixed(2)) : 0,
      plastic_mix_cost_inr_m2: Number((balance.cost_inr_m3 / 7).toFixed(2)),
      conventional_cost_inr_m2: Number((conventional.cost_inr_m3 / 7).toFixed(2)),
      cost_saving_inr_m2: Number((saving / 7).toFixed(2)),
      product_yield_m2_per_m3: 7.0,
      plastic_kg_per_m3: balance.plastic_kg_m3,
      additive_kg_per_m3: balance.additive_kg_m3,
    },
    rag_analogues: [
      {
        rank: 1,
        id: 'PCA_LIT_082',
        author: 'Alkharisi & Dahish',
        year: 2025,
        journal: 'Construction and Building Materials',
        doi: '10.1016/j.conbuildmat.2025.132456',
        primary_application: 'paving_block_light',
        secondary_application: 'hollow_concrete_block',
        l2_distance: 0.142,
        properties: {
          compressive_strength_mpa: 24.2,
          density_kgm3: 2150,
          water_absorption_pct: 4.8,
        },
      },
      {
        rank: 2,
        id: 'PCA_LIT_039',
        author: 'Nayir & Yilmaz',
        year: 2024,
        journal: 'Journal of Cleaner Production',
        doi: '10.1016/j.jclepro.2024.140892',
        primary_application: 'plastic_sand_paver',
        secondary_application: 'floor_tile_outdoor',
        l2_distance: 0.218,
        properties: {
          compressive_strength_mpa: 21.6,
          density_kgm3: 2080,
          water_absorption_pct: 5.2,
        },
      },
      {
        rank: 3,
        id: 'PCA_LIT_012',
        author: 'Chong & Shi',
        year: 2023,
        journal: 'Cement and Concrete Composites',
        doi: '10.1016/j.cemconcomp.2023.105128',
        primary_application: 'structural_concrete',
        secondary_application: 'paving_block_heavy',
        l2_distance: 0.295,
        properties: {
          compressive_strength_mpa: 28.4,
          density_kgm3: 2260,
          water_absorption_pct: 3.9,
        },
      },
    ],
    use_class_gates: classGates,
    primary_gate_status: gate.status,
    primary_gate_message: gate.message,
    verification_applications: classGates
      .filter((item) => item.status === 'verification_batch')
      .flatMap((item) => item.applications),
    source: 'demo',
  };
}

// ── API Functions ─────────────────────────────────────────────────────────────

export async function predictProperties(mix: MixInput): Promise<PredictionResponse> {
  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mix),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { ...data, source: 'live' };
  } catch (err) {
    console.warn('FastAPI unavailable, using client-side inference engine:', err);
    return generateMockPrediction(mix);
  }
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
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.mean || 25,
    flexural_strength_mpa: pred.predictions.flexural_strength_mpa?.mean || 3.5,
    split_tensile_mpa: pred.predictions.split_tensile_mpa?.mean || 2.2,
    density_kgm3: pred.predictions.density_kgm3?.mean || 2200,
    water_absorption_pct: pred.predictions.water_absorption_pct?.mean || 4.5,
    thermal_conductivity_wm: pred.predictions.thermal_conductivity_wm?.mean || 1.1,
    durability_index: pred.predictions.durability_index?.mean || 70,
    ...confidenceBounds(pred),
  };
}

export async function scoreSustainability(mix: MixInput, pred: PredictionResponse): Promise<ScoreResponse> {
  try {
    const res = await fetch(`${API_BASE}/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(propertyPayload(mix, pred)),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { ...data, source: 'live' };
  } catch (err) {
    console.warn('FastAPI /score unavailable, using client fallback:', err);
    return generateMockScore(mix, pred);
  }
}

export async function recommendApplications(mix: MixInput, pred: PredictionResponse): Promise<RecommendationResponse> {
  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(propertyPayload(mix, pred)),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { ...data, source: 'live' };
  } catch (err) {
    console.warn('FastAPI /recommend unavailable, using client fallback:', err);
    return generateMockRecommendation(mix, pred);
  }
}

function demoOptimize(req: OptimizeRequest): OptimizeResponse {
  const plastics = req.plastic_type ? [req.plastic_type] : ['PET', 'HDPE', 'LDPE', 'PVC', 'PP', 'Mixed'];
  const additives = ['none', 'fly_ash', 'silica_fume'];
  const reps: number[] = [];
  for (let rep = 0; rep <= req.replacement_pct_max + 0.001; rep += 5) reps.push(Math.min(rep, req.replacement_pct_max));
  const found: Array<{ mix: MixInput; cs: number; csLow: number; balance: ReturnType<typeof computeMassBalance>; score: number }> = [];

  for (const plastic of plastics) {
    for (const additive of additives) {
      for (const rep of reps) {
        for (const wc of [0.4, 0.5]) {
          const mix: MixInput = {
            plastic_type: plastic,
            replacement_pct: rep,
            particle_size_mm: 4,
            wc_ratio: wc,
            additive_type: additive,
            additive_pct: additive === 'none' ? 0 : 10,
            curing_temp_c: 27,
            curing_days: 28,
          };
          const pred = generateMockPrediction(mix);
          const cs = pred.predictions.compressive_strength_mpa.mean ?? 0;
          const csLow = pred.predictions.compressive_strength_mpa.ci_90_low ?? cs;
          const balance = computeMassBalance(mix);
          if (cs < req.compressive_strength_min) continue;
          if (req.cost_max_inr_per_m3 != null && balance.cost_inr_m3 > req.cost_max_inr_per_m3) continue;
          if (req.plastic_diversion_min_kg_m3 != null && balance.plastic_kg_m3 < req.plastic_diversion_min_kg_m3) continue;
          if (req.use_class) {
            const classGates = evaluateUseClasses(
              {
                compressive_strength_mpa: cs,
                water_absorption_pct: pred.predictions.water_absorption_pct?.mean,
                density_kgm3: pred.predictions.density_kgm3?.mean,
              },
              {
                compressive_strength_mpa: csLow,
                water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_low,
                density_kgm3: pred.predictions.density_kgm3?.ci_90_low,
              },
              {
                compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.ci_90_high,
                water_absorption_pct: pred.predictions.water_absorption_pct?.ci_90_high,
                density_kgm3: pred.predictions.density_kgm3?.ci_90_high,
              },
            );
            const gate = classGates.find((item) => item.id === req.use_class);
            if (!gate || (gate.status !== 'allowed' && gate.status !== 'lab_trial')) continue;
          }
          const score = req.weight_compressive * (cs / 60)
            + req.weight_cost * (1 - Math.min(balance.cost_inr_m3 / 9000, 1))
            + req.weight_co2 * (1 - Math.min(Math.max(balance.co2_kgco2e_m3, 0) / 400, 1))
            + req.weight_plastic_content * Math.min(balance.plastic_kg_m3 / 180, 1);
          found.push({ mix, cs, csLow, balance, score });
        }
      }
    }
  }

  const toPoint = (label: string, selected: boolean, row: (typeof found)[number]): TradeoffPoint => ({
    label,
    selected,
    predicted_cs_mpa: row.cs,
    predicted_cs_low: row.csLow,
    predicted_cost_inr_m3: row.balance.cost_inr_m3,
    predicted_co2_kgco2e_m3: row.balance.co2_kgco2e_m3,
    predicted_plastic_diversion_kg_m3: row.balance.plastic_kg_m3,
    recipe: {
      plastic_type: row.mix.plastic_type,
      additive_type: row.mix.additive_type,
      replacement_pct: row.mix.replacement_pct,
      particle_size_mm: row.mix.particle_size_mm,
      wc_ratio: row.mix.wc_ratio,
      additive_pct: row.mix.additive_pct,
      curing_temp_c: row.mix.curing_temp_c,
      curing_days: row.mix.curing_days,
      cement_kg_m3: row.balance.cement_kg_m3,
      sand_kg_m3: row.balance.sand_kg_m3,
      coarse_agg_kg_m3: row.balance.coarse_agg_kg_m3,
      plastic_kg_m3: row.balance.plastic_kg_m3,
      water_kg_m3: row.balance.water_kg_m3,
      additive_kg_m3: row.balance.additive_kg_m3,
    },
  });

  if (!found.length) {
    const fallbackMix: MixInput = {
      ...DEFAULT_MIX,
      plastic_type: req.plastic_type || 'PET',
      replacement_pct: Math.min(req.replacement_pct_max, 15),
    };
    const balance = computeMassBalance(fallbackMix);
    const pred = generateMockPrediction(fallbackMix);
    const row = {
      mix: fallbackMix,
      cs: pred.predictions.compressive_strength_mpa.mean ?? 0,
      csLow: pred.predictions.compressive_strength_mpa.ci_90_low ?? 0,
      balance,
      score: 0,
    };
    return {
      best_mix: toPoint('balanced', true, row).recipe,
      predicted_cs_mpa: row.cs,
      predicted_cs_low: row.csLow,
      predicted_cost_inr_m3: balance.cost_inr_m3,
      predicted_co2_kgco2e_m3: balance.co2_kgco2e_m3,
      predicted_plastic_diversion_kg_m3: balance.plastic_kg_m3,
      composite_score: 0,
      mode: req.mode,
      feasible: false,
      prediction_source: 'demo',
      mass_balance: balance,
      tradeoff_points: [toPoint('balanced', true, row)],
      source: 'demo',
    };
  }

  const balanced = found.reduce((best, row) => (row.score > best.score ? row : best), found[0]);
  const strongest = found.reduce((best, row) => (row.cs > best.cs ? row : best), found[0]);
  const diverted = found.reduce((best, row) => (row.balance.plastic_kg_m3 > best.balance.plastic_kg_m3 ? row : best), found[0]);
  const cheapest = found.reduce((best, row) => (row.balance.cost_inr_m3 < best.balance.cost_inr_m3 ? row : best), found[0]);
  const points = [toPoint('balanced', true, balanced)];
  for (const [label, row] of [['max_strength', strongest], ['max_diversion', diverted], ['min_cost', cheapest]] as const) {
    if (points.length >= 3) break;
    if (points.some((point) => point.recipe.plastic_type === row.mix.plastic_type && point.recipe.replacement_pct === row.mix.replacement_pct && point.recipe.wc_ratio === row.mix.wc_ratio && point.recipe.additive_type === row.mix.additive_type)) continue;
    points.push(toPoint(label, false, row));
  }

  return {
    best_mix: points[0].recipe,
    predicted_cs_mpa: balanced.cs,
    predicted_cs_low: balanced.csLow,
    predicted_cost_inr_m3: balanced.balance.cost_inr_m3,
    predicted_co2_kgco2e_m3: balanced.balance.co2_kgco2e_m3,
    predicted_plastic_diversion_kg_m3: balanced.balance.plastic_kg_m3,
    composite_score: Number(balanced.score.toFixed(4)),
    mode: req.mode,
    feasible: true,
    prediction_source: 'demo',
    mass_balance: balanced.balance,
    tradeoff_points: points,
    use_class: req.use_class,
    source: 'demo',
  };
}

export async function runOptimization(req: OptimizeRequest): Promise<OptimizeResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
  } catch (err) {
    console.warn('FastAPI /optimize unavailable, using demo search:', err);
    return demoOptimize(req);
  }
  if (res.status === 422) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: unknown }).detail;
    const message = typeof detail === 'string'
      ? detail
      : 'The optimiser rejected this request. Weights must sum to 1 and mode must be constrained or scenario.';
    throw new Error(message);
  }
  if (!res.ok) {
    console.warn(`FastAPI /optimize returned ${res.status}, using demo search`);
    return demoOptimize(req);
  }
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
  try {
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `plasticrete_report_${sessionId || 'mix'}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return true;
  } catch (err) {
    console.warn('PDF report API unavailable:', err);
    return false;
  }
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
  if (!res.ok) throw new Error(`Could not save the batch (HTTP ${res.status}).`);
  return res.json();
}

export async function fetchBatch(id: string): Promise<SavedBatch> {
  const res = await fetch(`${API_BASE}/batches/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(res.status === 404 ? 'Batch not found.' : `HTTP ${res.status}`);
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
  if (!res.ok) throw new Error(`Could not save the lab result (HTTP ${res.status}).`);
  return res.json();
}

export async function uploadBatchPhoto(id: string, file: File): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/batches/${encodeURIComponent(id)}/photo`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`Photo upload failed (HTTP ${res.status}).`);
}

export function batchPhotoUrl(id: string): string {
  return `${API_BASE}/batches/${encodeURIComponent(id)}/photo`;
}

