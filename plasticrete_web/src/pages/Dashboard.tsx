import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { GaugeChart } from '../components/GaugeChart';
import {
  Activity,
  Leaf,
  Sparkles,
  Boxes,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

export const Dashboard: React.FC = () => {
  const { prediction, score, recommendation, setStudioTab } = useMix();

  const cs = prediction?.predictions.compressive_strength_mpa?.mean || 0;
  const csLow = prediction?.predictions.compressive_strength_mpa?.ci_90_low || 0;
  const csHigh = prediction?.predictions.compressive_strength_mpa?.ci_90_high || 0;
  const co2Saving = score?.co2_saving_pct || 0;
  const diversionKg = score?.plastic_diversion_kg_m3 || 0;
  const primaryApp = recommendation?.primary_application || 'paving_block_light';
  const confidence = recommendation?.primary_confidence_pct || 0;

  // Radar chart data comparing current plastic mix vs conventional M20 concrete benchmark
  const radarData = [
    {
      subject: 'Comp. Strength',
      PlasticMix: Math.min(100, Math.round((cs / 35.0) * 100)),
      M20Benchmark: 70,
    },
    {
      subject: 'Flexural',
      PlasticMix: Math.min(100, Math.round(((prediction?.predictions.flexural_strength_mpa?.mean || 3.5) / 4.5) * 100)),
      M20Benchmark: 65,
    },
    {
      subject: 'Low Carbon',
      PlasticMix: Math.min(100, Math.max(20, Math.round(co2Saving * 2.5))),
      M20Benchmark: 30,
    },
    {
      subject: 'Diversion',
      PlasticMix: Math.min(100, Math.round((diversionKg / 200.0) * 100)),
      M20Benchmark: 5,
    },
    {
      subject: 'Lightweight',
      PlasticMix: Math.min(100, Math.round((2400.0 / (prediction?.predictions.density_kg_m3?.mean || 2300)) * 75)),
      M20Benchmark: 70,
    },
    {
      subject: 'Workability',
      PlasticMix: Math.min(100, Math.round(((prediction?.predictions.slump_mm?.mean || 75) / 120.0) * 100)),
      M20Benchmark: 60,
    },
  ];

  const APPLICATION_PRETTY_NAMES: Record<string, string> = {
    paving_block_light: 'Interlocking Paver Block (Light Traffic)',
    hollow_block_non_load: 'Hollow Concrete Masonry Unit (Non-Load)',
    solid_block_load: 'Solid Precast Load-Bearing Block',
    drainage_cover: 'Precast Stormwater Drain Cover Slab',
    curbstone: 'Roadway Kerbstone & Channel (IS 5758)',
    boundary_wall_panel: 'Precast Boundary Wall Panel',
  };

  return (
    <div className="space-y-6">
      {/* Top Mix Design Input Drawer */}
      <MixControlPanel />

      {/* Uncertainty Notice if flagged */}
      {prediction?.uncertainty_flag && (
        <div className="p-3.5 rounded-xl bg-amber-100 border border-amber-300 flex items-center gap-2.5 text-xs text-amber-950 font-medium">
          <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0" />
          <span>
            <strong>Extrapolation Notice:</strong> High plastic volume (&gt;30%) or extreme w/c ratio enters low-density training distribution. Confidence intervals have widened accordingly.
          </span>
        </div>
      )}

      {/* 4 Core KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Compressive Strength */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-800 mb-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Compressive Strength</span>
            <div className="p-1.5 rounded-lg bg-blue-100 text-blue-700">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-extrabold font-mono text-slate-950">
                {cs}
              </span>
              <span className="text-xs font-bold text-slate-600 font-mono">MPa</span>
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              90% CI: [{csLow} – {csHigh}] MPa
            </p>
          </div>
          <button
            onClick={() => setStudioTab('optimizer')}
            className="mt-3 pt-2 border-t border-slate-200 text-xs font-bold text-blue-700 flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>Run Pareto Optimizer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* KPI 2: Embodied Carbon Saved */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-800 mb-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Embodied Carbon Saved</span>
            <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-800">
              <Leaf className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-extrabold font-mono text-emerald-700">
                -{co2Saving}%
              </span>
              <span className="text-xs font-bold text-slate-600 font-mono">vs M20</span>
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              {score?.embodied_carbon_kgco2e_m3} kg CO₂e / m³
            </p>
          </div>
          <button
            onClick={() => setStudioTab('sustainability')}
            className="mt-3 pt-2 border-t border-slate-200 text-xs font-bold text-emerald-700 flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>LCA & BIS Details</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* KPI 3: Plastic Waste Diverted */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-800 mb-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Plastic Waste Diverted</span>
            <div className="p-1.5 rounded-lg bg-cyan-100 text-cyan-800">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-extrabold font-mono text-cyan-800">
                {diversionKg}
              </span>
              <span className="text-xs font-bold text-slate-600 font-mono">kg/m³</span>
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              ≈ {(score?.pet_bottle_equiv || 0).toLocaleString()} PET bottles / m³
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
            <span>Circular Economy metric</span>
          </div>
        </div>

        {/* KPI 4: Optimal Construction Use */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-800 mb-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Optimal Construction Use</span>
            <div className="p-1.5 rounded-lg bg-indigo-100 text-indigo-800">
              <Boxes className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-sm font-bold text-slate-950 line-clamp-1">
              {APPLICATION_PRETTY_NAMES[primaryApp] || primaryApp}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-xs font-mono font-bold text-indigo-700">
                {confidence}% Confidence
              </span>
              <span className="text-xs font-semibold text-slate-600">by RF + FAISS</span>
            </div>
          </div>
          <button
            onClick={() => setStudioTab('recommender')}
            className="mt-3 pt-2 border-t border-slate-200 text-xs font-bold text-indigo-700 flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>View Literature Analogues</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Middle Grid: Radar Chart + Sustainability Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Radar Comparison (2 Cols) */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <h3 className="font-bold text-slate-950 text-base">
                Engineering Performance Profile (Multi-Target Radar)
              </h3>
              <p className="text-xs font-medium text-slate-700">
                Normalized index comparing current Plastic-Waste Composite vs Conventional M20 concrete
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-semibold">
              <span className="flex items-center gap-1.5 text-emerald-800">
                <span className="w-3 h-3 rounded-full bg-emerald-600" />
                <span>Plastic Mix</span>
              </span>
              <span className="flex items-center gap-1.5 text-slate-700">
                <span className="w-3 h-3 rounded-full bg-slate-400" />
                <span>M20 Baseline</span>
              </span>
            </div>
          </div>

          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#cbd5e1" strokeDasharray="3 3" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#1e293b', fontSize: 12, fontWeight: 600 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569', fontSize: 10, fontWeight: 500 }} />
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, fontSize: 12, fontWeight: 600, border: '1px solid #cbd5e1', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} />
                <Radar
                  name="M20 Baseline"
                  dataKey="M20Benchmark"
                  stroke="#64748b"
                  fill="#94a3b8"
                  fillOpacity={0.25}
                />
                <Radar
                  name="Plastic Mix"
                  dataKey="PlasticMix"
                  stroke="#047857"
                  fill="#10b981"
                  fillOpacity={0.45}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sustainability Score Gauge (1 Col) */}
        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="pb-3 border-b border-slate-200">
            <h3 className="font-bold text-slate-950 text-base">
              Sustainability & Compliance Score
            </h3>
            <p className="text-xs font-medium text-slate-700">
              Composite index based on LCA carbon, green rating & BIS IS 1237
            </p>
          </div>

          <div className="py-2">
            <GaugeChart
              value={score?.sustainability_score || 0}
              label="Overall Sustainability Score"
              grade={score?.sustainability_grade || 'B'}
              sublabel="Target: Grade A (>=75)"
              size={170}
            />
          </div>

          <div className="space-y-2 pt-3 border-t border-slate-200 text-xs">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-800">BIS IS 1237 Compliance:</span>
              <span className={`font-bold flex items-center gap-1 ${score?.bis_overall_pass ? 'text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded' : 'text-amber-900 bg-amber-100 px-2 py-0.5 rounded'}`}>
                <ShieldCheck className="w-3.5 h-3.5" />
                {score?.bis_overall_pass ? 'PASSED' : 'CHECK NEEDED'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-800">Green Rating Credits:</span>
              <span className="font-mono font-bold text-slate-950">
                {score?.total_green_credits || 0} pts (IGBC/GRIHA/LEED)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
