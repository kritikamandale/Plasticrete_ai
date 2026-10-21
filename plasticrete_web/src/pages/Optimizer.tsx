import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import { runOptimization } from '../api/client';
import type { OptimizeResponse } from '../types';
import {
  SlidersHorizontal,
  Sparkles,
  CheckCircle2,
  Zap,
} from 'lucide-react';

export const Optimizer: React.FC = () => {
  const { setMix, setStudioTab } = useMix();

  // Constraints
  const [repMax, setRepMax] = useState<number>(25.0);
  const [csMin, setCsMin] = useState<number>(20.0);
  const [plasticType, setPlasticType] = useState<string>('Any');

  // Weights (must sum to 1.0)
  const [wCS, setWCS] = useState<number>(0.40);
  const [wCost, setWCost] = useState<number>(0.30);
  const [wCo2, setWCo2] = useState<number>(0.20);
  const [wPlastic, setWPlastic] = useState<number>(0.10);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<OptimizeResponse | null>(null);

  const handleRunOptimizer = async () => {
    setLoading(true);
    try {
      const data = await runOptimization({
        mode: 'multi_objective',
        plastic_type: plasticType === 'Any' ? null : plasticType,
        replacement_pct_max: repMax,
        compressive_strength_min: csMin,
        weight_compressive: wCS,
        weight_cost: wCost,
        weight_co2: wCo2,
        weight_plastic_content: wPlastic,
      });
      setResult(data);
    } catch (e) {
      console.error('Optimization error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyMix = () => {
    if (!result) return;
    const bm = result.best_mix;
    setMix((prev) => ({
      ...prev,
      plastic_type: plasticType === 'Any' ? 'PET' : plasticType,
      replacement_pct: bm.replacement_pct || 15.0,
      particle_size_mm: bm.particle_size_mm || 4.0,
      wc_ratio: bm.wc_ratio || 0.45,
      additive_pct: bm.additive_pct || 10.0,
      curing_temp_c: bm.curing_temp_c || 27.0,
      curing_days: Math.round(bm.curing_days || 28),
    }));
    setStudioTab('overview');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-slate-950">
              M2 Intelligent Mix Optimiser (Surrogate-Guided Optuna)
            </h2>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-900 border border-indigo-300">
              <Sparkles className="w-3.5 h-3.5" />
              Pareto Frontier
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-700 mt-1">
            Constrained Bayesian optimisation balancing Compressive Strength, Production Cost, Embodied CO₂, and Plastic Diversion
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Objective Weights Card */}
          <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-emerald-700" />
                <h3 className="font-bold text-slate-950 text-sm">
                  Objective Trade-off Weights
                </h3>
              </div>
              <span className="text-xs font-mono font-bold text-slate-700">
                Sum: {(wCS + wCost + wCo2 + wPlastic).toFixed(2)} / 1.00
              </span>
            </div>

            <div className="space-y-4 text-xs font-semibold">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900">Compressive Strength</span>
                  <span className="font-mono font-bold text-emerald-800">{(wCS * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={wCS}
                  onChange={(e) => setWCS(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900">Cost Reduction</span>
                  <span className="font-mono font-bold text-blue-800">{(wCost * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={wCost}
                  onChange={(e) => setWCost(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900">CO₂ Footprint Reduction</span>
                  <span className="font-mono font-bold text-cyan-800">{(wCo2 * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={wCo2}
                  onChange={(e) => setWCo2(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-cyan-600"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900">Plastic Diversion Maximization</span>
                  <span className="font-mono font-bold text-indigo-800">{(wPlastic * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={wPlastic}
                  onChange={(e) => setWPlastic(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>
            </div>
          </div>

          {/* Hard Constraints Card */}
          <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
            <h3 className="font-bold text-slate-950 text-sm mb-3 pb-2 border-b border-slate-200">
              Feasibility & Boundary Constraints
            </h3>

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-900 font-bold block mb-1">
                  Target Plastic Polymer
                </label>
                <select
                  value={plasticType}
                  onChange={(e) => setPlasticType(e.target.value)}
                  className="w-full text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-900 px-3 py-1.5 shadow-sm"
                >
                  <option value="Any">Any Polymer (Global Pareto Search)</option>
                  <option value="PET">PET (Bottles & Containers)</option>
                  <option value="HDPE">HDPE (Pipes & Caps)</option>
                  <option value="LDPE">LDPE (Bags & Films)</option>
                  <option value="PVC">PVC (Pipes & Conduits)</option>
                  <option value="PP">PP (Automotive & Crates)</option>
                  <option value="Mixed">Mixed Post-Consumer Waste</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900 font-semibold">Max Allowed Replacement %</span>
                  <span className="font-mono font-bold text-slate-950">{repMax}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="40"
                  step="1"
                  value={repMax}
                  onChange={(e) => setRepMax(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-slate-900 font-semibold">Min Compressive Strength (Hard Barrier)</span>
                  <span className="font-mono font-bold text-slate-950">{csMin} MPa</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="40"
                  step="1"
                  value={csMin}
                  onChange={(e) => setCsMin(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
              </div>
            </div>

            <button
              onClick={handleRunOptimizer}
              disabled={loading}
              className="mt-5 w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition-all disabled:opacity-50 cursor-pointer"
            >
              <Zap className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Solving Pareto Front (Optuna)...' : 'Run Mix Optimization'}</span>
            </button>
          </div>
        </div>

        {/* Results Column (7 cols) */}
        <div className="lg:col-span-7">
          {result ? (
            <div className="glass-card rounded-2xl p-6 border border-slate-300/80 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200">
                <div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-700" />
                    <h3 className="font-bold text-slate-950 text-base">
                      Optimal Mix Solution Found
                    </h3>
                  </div>
                  <p className="text-xs font-semibold text-slate-700 mt-0.5">
                    Mode: {result.mode} · Composite Utility: {result.composite_score.toFixed(4)}
                  </p>
                </div>

                <button
                  onClick={handleApplyMix}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-bold hover:bg-emerald-200 transition-colors cursor-pointer"
                >
                  <span>Apply as Active Mix</span>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* 4 Outcome Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <span className="text-[11px] font-bold text-slate-700 block mb-1">Strength (CS)</span>
                  <span className="text-xl font-extrabold font-mono text-emerald-800">
                    {result.predicted_cs_mpa} MPa
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <span className="text-[11px] font-bold text-slate-700 block mb-1">Mix Cost</span>
                  <span className="text-xl font-extrabold font-mono text-blue-800">
                    ₹{result.predicted_cost_inr_m3} /m³
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <span className="text-[11px] font-bold text-slate-700 block mb-1">CO₂ Footprint</span>
                  <span className="text-xl font-extrabold font-mono text-cyan-800">
                    {result.predicted_co2_kgco2e_m3} kg
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <span className="text-[11px] font-bold text-slate-700 block mb-1">Plastic Diverted</span>
                  <span className="text-xl font-extrabold font-mono text-indigo-800">
                    {result.predicted_plastic_diversion_kg_m3} kg/m³
                  </span>
                </div>
              </div>

              {/* Optimized Mix Design Proportions */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3">
                  Optimal Formulation Recipe
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs font-mono">
                  {Object.entries(result.best_mix).map(([param, val]) => (
                    <div key={param} className="p-2.5 rounded-lg border border-slate-200 bg-white flex justify-between">
                      <span className="text-slate-700 font-semibold">{param}:</span>
                      <span className="font-bold text-slate-950">{val}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-12 text-center rounded-2xl border-2 border-dashed border-slate-300 text-slate-600 bg-white/50">
              <Sparkles className="w-10 h-10 mb-3 text-slate-500" />
              <h3 className="text-base font-bold text-slate-900">
                No Optimization Run Yet
              </h3>
              <p className="text-xs font-semibold text-slate-700 max-w-sm mt-1">
                Configure your objective weights and feasibility limits on the left, then click "Run Mix Optimization".
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
