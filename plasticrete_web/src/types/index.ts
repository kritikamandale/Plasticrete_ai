export interface MixInput {
  plastic_type: string;
  replacement_pct: number;
  particle_size_mm: number;
  wc_ratio: number;
  additive_type: string;
  additive_pct: number;
  curing_temp_c: number;
  curing_days: number;
}

export interface PropertyResult {
  mean: number | null;
  ci_90_low: number | null;
  ci_90_high: number | null;
}

export interface PredictionResponse {
  predictions: Record<string, PropertyResult>;
  shap_values: Record<string, Record<string, number>>;
  uncertainty_flag: boolean;
  low_coverage_targets: string[];
}

export interface ScoreResponse {
  sustainability_score: number;
  sustainability_grade: string;
  embodied_carbon_kgco2e_m3: number;
  co2_saving_pct: number;
  plastic_diversion_kg_m3: number;
  pet_bottle_equiv: number;
  bis_overall_pass: boolean;
  igbc_total_credits: number;
  griha_material_criterion_pts: number;
  leed_total_points: number;
  total_green_credits: number;
  top_negative_factor: string;
  remediation_action_1: string;
  remediation_action_2: string;
  remediation_action_3: string;
  estimated_score_gain: number;
}

export interface RAGAnalogue {
  rank: number;
  id: string;
  author: string;
  year: number;
  journal: string;
  doi: string;
  primary_application: string;
  secondary_application: string;
  l2_distance: number;
  properties: Record<string, number>;
}

export interface CostBenefit {
  plastic_mix_cost_inr_m3: number;
  conventional_cost_inr_m3: number;
  cost_saving_inr_m3: number;
  cost_saving_pct: number;
  plastic_mix_cost_inr_m2: number;
  conventional_cost_inr_m2: number;
  cost_saving_inr_m2: number;
  product_yield_m2_per_m3: number;
  plastic_kg_per_m3: number;
  additive_kg_per_m3: number;
}

export interface RecommendationResponse {
  primary_application: string;
  primary_confidence_pct: number;
  suitable_applications: string[];
  suitability_scores: Record<string, number>;
  cost_benefit: CostBenefit;
  rag_analogues: RAGAnalogue[];
}

export interface OptimizeRequest {
  plastic_type?: string | null;
  replacement_pct_max: number;
  compressive_strength_min: number;
  density_max_kgm3?: number | null;
  cost_max_inr_per_m3?: number | null;
  weight_compressive: number;
  weight_cost: number;
  weight_co2: number;
  weight_plastic_content: number;
  mode: string;
}

export interface OptimizeResponse {
  best_mix: Record<string, number>;
  predicted_cs_mpa: number;
  predicted_cost_inr_m3: number;
  predicted_co2_kgco2e_m3: number;
  predicted_plastic_diversion_kg_m3: number;
  composite_score: number;
  mode: string;
}

export const TARGET_LABELS: Record<string, { label: string; unit: string; description: string }> = {
  compressive_strength_mpa: { label: 'Compressive Strength', unit: 'MPa', description: 'Resistance to crushing force' },
  flexural_strength_mpa: { label: 'Flexural Strength', unit: 'MPa', description: 'Resistance to bending stresses' },
  split_tensile_mpa: { label: 'Split Tensile Strength', unit: 'MPa', description: 'Tensile capacity under diametral load' },
  density_kgm3: { label: 'Bulk Density', unit: 'kg/m³', description: 'Weight per unit volume' },
  water_absorption_pct: { label: 'Water Absorption', unit: '%', description: 'Moisture uptake by mass' },
  thermal_conductivity_wm: { label: 'Thermal Conductivity', unit: 'W/m·K', description: 'Heat transfer rate' },
  durability_index: { label: 'Durability Index', unit: '/100', description: 'Resistance to freeze-thaw & sulfate attack' },
};

export const APPLICATION_PRETTY_NAMES: Record<string, string> = {
  paving_block_light: 'Light Paving Blocks (Footpaths & Patios)',
  paving_block_heavy: 'Heavy Duty Pavers (Commercial Traffic)',
  floor_tile_indoor: 'Indoor Flooring Tiles',
  floor_tile_outdoor: 'Outdoor Patio & Walkway Tiles',
  hollow_concrete_block: 'Hollow Concrete Masonry Blocks',
  lightweight_partition_block: 'Lightweight Partition Wall Blocks',
  structural_concrete: 'Structural Concrete (Beams/Columns)',
  nonstructural_concrete_fill: 'Non-Structural Concrete Fill & Sub-base',
  plastic_sand_paver: 'Plastic-Sand Composite Paver',
  wall_cladding_panel: 'Exterior Wall Cladding Panels',
  thermal_insulation_panel: 'Thermal & Acoustic Insulation Panels',
  kerb_stone: 'Roadside Kerb & Gutter Stones',
};
