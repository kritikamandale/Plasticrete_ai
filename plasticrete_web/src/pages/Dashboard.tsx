import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { GaugeChart } from '../components/GaugeChart';
import {
  Activity,
  Leaf,
  Sparkles,
  Boxes,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { APPLICATION_PRETTY_NAMES, TARGET_LABELS } from '../types';

function shown(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
}

export const Dashboard: React.FC = () => {
  const { prediction, score, recommendation, setStudioTab } = useMix();

  const compressive = prediction?.predictions.compressive_strength_mpa;
  const co2Saving = score?.co2_saving_pct;
  const diversionKg = score?.plastic_diversion_kg_m3;
  const primaryApp = recommendation?.primary_application;
  const confidence = recommendation?.primary_confidence_pct;

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
                {shown(compressive?.mean)}
              </span>
              <span className="text-xs font-bold text-slate-600 font-mono">MPa</span>
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              90% CI: [{shown(compressive?.ci_90_low)} – {shown(compressive?.ci_90_high)}] MPa
            </p>
          </div>
          <button
            onClick={() => setStudioTab('optimizer')}
            className="mt-3 pt-2 border-t border-slate-200 text-xs font-bold text-blue-700 flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>Search mixes</span>
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
                {co2Saving == null ? '—' : `${co2Saving}%`}
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
            <span>Mass balance</span>
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
                {shown(diversionKg)}
              </span>
              <span className="text-xs font-bold text-slate-600 font-mono">kg/m³</span>
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              {score?.pet_bottle_equiv == null ? '—' : score.pet_bottle_equiv.toLocaleString()} bottle equivalents / m³
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
              {primaryApp ? (APPLICATION_PRETTY_NAMES[primaryApp] || primaryApp) : '—'}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-xs font-mono font-bold text-indigo-700">
                {confidence == null ? '—' : `${confidence}% match`}
              </span>
              <span className="text-xs font-semibold text-slate-600">{recommendation?.primary_gate_message || 'Waiting for the model'}</span>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
          <div className="pb-3 border-b border-slate-200 mb-3">
            <h3 className="font-bold text-slate-950 text-base">M1 property means</h3>
            <p className="text-xs font-medium text-slate-700">
              Seven outputs from the ensemble, with the 90% interval when the model returned one.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {Object.entries(TARGET_LABELS).map(([key, meta]) => {
              const result = prediction?.predictions[key];
              return (
                <div key={key} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-[11px] font-bold text-slate-700">{meta.label}</p>
                  <p className="font-mono text-sm font-bold text-slate-950">
                    {shown(result?.mean)} {meta.unit}
                  </p>
                  <p className="text-[11px] font-mono text-slate-600">
                    {shown(result?.ci_90_low)} – {shown(result?.ci_90_high)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="pb-3 border-b border-slate-200">
            <h3 className="font-bold text-slate-950 text-base">Use-class gate</h3>
            <p className="text-xs font-medium text-slate-700">
              Allowed only when that product's standard clears on the conservative side of the interval.
            </p>
          </div>

          {score?.sustainability_score != null && (
            <div className="py-2">
              <GaugeChart
                value={score.sustainability_score}
                label="Sustainability index"
                grade={score.sustainability_grade}
                sublabel="Carbon, plastic mass, and cleared gates. Rating points are not added."
                size={170}
              />
            </div>
          )}

          <div className="space-y-2 pt-3 border-t border-slate-200 text-xs">
            {(score?.use_class_gates || []).map((gate) => (
              <div key={gate.id} className="flex justify-between items-center gap-2">
                <span className="font-bold text-slate-800">{gate.label}</span>
                <span className="font-bold text-slate-950">{gate.status.replace('_', ' ')}</span>
              </div>
            ))}
            {!score && <p className="font-semibold text-slate-700">Waiting for the model.</p>}
          </div>
        </div>
      </div>
    </div>
  );
};
