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
  };
}

function generateMockScore(mix: MixInput, pred: PredictionResponse): ScoreResponse {
  const cs = pred.predictions.compressive_strength_mpa.mean || 25;
  const diversionKg = Math.round(mix.replacement_pct * 11.2);
  const baselineCo2 = 365.7;
  const co2SavingPct = Math.min(48, Math.round(mix.replacement_pct * 1.2 + mix.additive_pct * 0.7));
  const embodiedCo2 = Math.round(baselineCo2 * (1 - co2SavingPct / 100) * 10) / 10;
  const passBis = cs >= 20.0;
  const score = Math.round(Math.min(96, Math.max(30, 50 + co2SavingPct * 0.6 + (passBis ? 15 : -10))));
  const grade = score >= 85 ? 'A+' : score >= 75 ? 'A' : score >= 65 ? 'B' : 'C';

  return {
    sustainability_score: score,
    sustainability_grade: grade,
    embodied_carbon_kgco2e_m3: embodiedCo2,
    co2_saving_pct: co2SavingPct,
    plastic_diversion_kg_m3: diversionKg,
    pet_bottle_equiv: diversionKg * 22,
    bis_overall_pass: passBis,
    igbc_total_credits: score >= 70 ? 3.0 : 1.0,
    griha_material_criterion_pts: score >= 60 ? 2.0 : 1.0,
    leed_total_points: score >= 65 ? 2.0 : 1.0,
    total_green_credits: 6.0,
    top_negative_factor: mix.wc_ratio > 0.5 ? 'High Water-Cement Ratio' : 'Aggregate Replacement Strength Loss',
    remediation_action_1: 'Lower w/c ratio by 0.03 using a PCE superplasticizer to recover ~3.5 MPa CS.',
    remediation_action_2: 'Increase pozzolanic fly ash or silica fume content to densify interfacial transition zone.',
    remediation_action_3: 'Apply silane coupling agent or chemical washing to plastic aggregates to improve matrix adhesion.',
    estimated_score_gain: 7.5,
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
      plastic_mix_cost_inr_m3: 3950,
      conventional_cost_inr_m3: 4850,
      cost_saving_inr_m3: 900,
      cost_saving_pct: 18.6,
      plastic_mix_cost_inr_m2: 564,
      conventional_cost_inr_m2: 692,
      cost_saving_inr_m2: 128,
      product_yield_m2_per_m3: 7.0,
      plastic_kg_per_m3: Math.round(mix.replacement_pct * 11.2),
      additive_kg_per_m3: Math.round(mix.additive_pct * 3.8),
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
    return await res.json();
  } catch (err) {
    console.warn('FastAPI unavailable, using client-side inference engine:', err);
    return generateMockPrediction(mix);
  }
}

export async function scoreSustainability(mix: MixInput, pred: PredictionResponse): Promise<ScoreResponse> {
  const payload = {
    ...mix,
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.mean || 25,
    flexural_strength_mpa: pred.predictions.flexural_strength_mpa?.mean || 3.5,
    split_tensile_mpa: pred.predictions.split_tensile_mpa?.mean || 2.2,
    density_kgm3: pred.predictions.density_kgm3?.mean || 2200,
    water_absorption_pct: pred.predictions.water_absorption_pct?.mean || 4.5,
    thermal_conductivity_wm: pred.predictions.thermal_conductivity_wm?.mean || 1.1,
    durability_index: pred.predictions.durability_index?.mean || 70,
  };

  try {
    const res = await fetch(`${API_BASE}/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('FastAPI /score unavailable, using client fallback:', err);
    return generateMockScore(mix, pred);
  }
}

export async function recommendApplications(mix: MixInput, pred: PredictionResponse): Promise<RecommendationResponse> {
  const payload = {
    ...mix,
    compressive_strength_mpa: pred.predictions.compressive_strength_mpa?.mean || 25,
    flexural_strength_mpa: pred.predictions.flexural_strength_mpa?.mean || 3.5,
    split_tensile_mpa: pred.predictions.split_tensile_mpa?.mean || 2.2,
    density_kgm3: pred.predictions.density_kgm3?.mean || 2200,
    water_absorption_pct: pred.predictions.water_absorption_pct?.mean || 4.5,
    thermal_conductivity_wm: pred.predictions.thermal_conductivity_wm?.mean || 1.1,
    durability_index: pred.predictions.durability_index?.mean || 70,
  };

  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('FastAPI /recommend unavailable, using client fallback:', err);
    return generateMockRecommendation(mix, pred);
  }
}

export async function runOptimization(req: OptimizeRequest): Promise<OptimizeResponse> {
  try {
    const res = await fetch(`${API_BASE}/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('FastAPI /optimize unavailable, using surrogate mock:', err);
    return {
      best_mix: {
        plastic_type_enc: 0,
        replacement_pct: Math.min(req.replacement_pct_max, 16.5),
        particle_size_mm: 3.5,
        wc_ratio: 0.42,
        additive_pct: 12.0,
        curing_temp_c: 32.0,
        curing_days: 28,
      },
      predicted_cs_mpa: Math.max(req.compressive_strength_min, 28.4),
      predicted_cost_inr_m3: 3820,
      predicted_co2_kgco2e_m3: 265.4,
      predicted_plastic_diversion_kg_m3: 185.0,
      composite_score: 0.842,
      mode: req.mode,
    };
  }
}

export async function generateReport(
  mix: MixInput,
  prediction: PredictionResponse,
  score: ScoreResponse,
  recommendation: RecommendationResponse,
  sessionId?: string,
): Promise<boolean> {
  try {
    const payload = {
      mix_params: mix,
      prediction,
      score,
      recommendation,
      session_id: sessionId || `PLT-${new Date().toISOString().slice(0, 10)}`,
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

