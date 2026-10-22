import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { GaugeChart } from '../components/GaugeChart';
import {
  Award,
  Sparkles,
  TrendingDown,
} from 'lucide-react';

export const Sustainability: React.FC = () => {
  const { score } = useMix();
  const baseline = score?.mass_balance?.baseline_co2_kgco2e_m3;

  return (
    <div className="space-y-6">
      <MixControlPanel />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">
            M3 Sustainability, LCA & BIS Compliance Engine
          </h2>
          <p className="text-xs font-semibold text-slate-700">
            One mass-balance table for cement, sand, coarse aggregate, plastic, water, cost, and kg CO₂e. Each product waits for its own standard.
          </p>
        </div>
      </div>

      {/* Top 3 Cards Grid: Score Gauge, Carbon Accounting, Diversion Counter */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Score Gauge Card */}
        <div className="glass-card rounded-2xl p-5 flex flex-col items-center justify-between border border-slate-300/80 shadow-sm">
          <div className="w-full pb-2 border-b border-slate-200 text-center">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Aggregate Sustainability Index</span>
          </div>
          {score?.sustainability_score == null ? (
            <p className="py-8 text-sm font-semibold text-slate-700">Waiting for the model.</p>
          ) : (
            <GaugeChart
              value={score.sustainability_score}
              grade={score.sustainability_grade}
              label="Sustainability index"
              sublabel="Carbon, plastic mass, and cleared gates. Rating points are not added."
              size={180}
            />
          )}
          <div className="w-full pt-3 border-t border-slate-200 text-center text-xs font-semibold text-slate-700">
            From the shared mass balance and the use-class gates.
          </div>
        </div>

        {/* Embodied Carbon Accounting */}
        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Embodied Carbon (Cradle-to-Gate)</span>
            <span className="text-xs font-mono font-bold text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300">
              {score?.co2_saving_pct == null ? '—' : `${score.co2_saving_pct}% vs baseline`}
            </span>
          </div>

          <div className="space-y-4 my-auto py-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-900 font-bold">Plastic Mix Carbon:</span>
                <span className="font-mono font-extrabold text-emerald-800">
                  {score?.embodied_carbon_kgco2e_m3} kg CO₂e/m³
                </span>
              </div>
              <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-600 rounded-full"
                  style={{ width: `${baseline && score?.embodied_carbon_kgco2e_m3 != null ? Math.min(100, (score.embodied_carbon_kgco2e_m3 / baseline) * 100) : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-900 font-bold">Conventional M20 Baseline:</span>
                <span className="font-mono font-bold text-slate-700">{baseline ?? '—'} kg CO₂e/m³</span>
              </div>
              <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-slate-500 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 flex items-center gap-2 text-xs font-semibold text-slate-800">
            <TrendingDown className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>Difference vs baseline: {baseline == null || score?.embodied_carbon_kgco2e_m3 == null ? '—' : (baseline - score.embodied_carbon_kgco2e_m3).toFixed(2)} kg CO₂e per cubic meter</span>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Recipe quantities</span>
            <div className="p-1 rounded bg-amber-100 text-amber-900">
              <Award className="w-4 h-4" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center my-auto py-2">
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Plastic</span>
              <span className="text-xl font-extrabold font-mono text-emerald-800">
                {score?.mass_balance?.plastic_kg_m3 ?? '—'}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">kg/m³</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">CO₂e</span>
              <span className="text-xl font-extrabold font-mono text-cyan-800">
                {score?.embodied_carbon_kgco2e_m3 ?? '—'}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">kg/m³</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Bottles</span>
              <span className="text-xl font-extrabold font-mono text-indigo-800">
                {score?.pet_bottle_equiv ?? '—'}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">equiv.</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 text-xs font-bold text-slate-800">
            These quantities come from the shared mass-balance table. This page does not file a green-building rating.
          </div>
        </div>
      </div>

      {/* Mass balance — the same numbers the optimiser and the PDF use */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 pb-3 border-b border-slate-200 mb-4">
          <div>
            <h3 className="font-bold text-slate-950 text-base">Mass balance</h3>
            <p className="text-xs font-semibold text-slate-700">
              {score?.mass_balance?.table_id || 'plasticrete-mass-balance-v1'} · factors dated {score?.mass_balance?.factor_date || '2026-03-01'}
            </p>
          </div>
          <p className="text-xs font-semibold text-slate-700 max-w-xl">
            Cement, sand, coarse aggregate, plastic, water, cost, and kg CO₂e from one table. A spreadsheet of these rows reproduces the total.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-300 text-slate-800 font-bold">
                <th className="pb-2 pr-3">Material</th>
                <th className="pb-2 pr-3">kg/m³</th>
                <th className="pb-2 pr-3">CO₂ factor</th>
                <th className="pb-2 pr-3">Source</th>
                <th className="pb-2 pr-3">Date</th>
                <th className="pb-2 pr-3">kg CO₂e</th>
                <th className="pb-2 text-right">₹</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {(score?.mass_balance?.rows || []).map((row) => (
                <tr key={row.material}>
                  <td className="py-2 font-semibold text-slate-950">{row.material}</td>
                  <td className="py-2 font-mono">{row.quantity_kg_m3.toFixed(2)}</td>
                  <td className="py-2 font-mono">{row.co2_factor_kg_per_kg}</td>
                  <td className="py-2 text-slate-700">{row.co2_factor_source}</td>
                  <td className="py-2 font-mono">{row.co2_factor_date}</td>
                  <td className="py-2 font-mono">{row.co2_kgco2e_m3.toFixed(2)}</td>
                  <td className="py-2 font-mono text-right">{row.cost_inr_m3.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-xs font-bold text-slate-900">
          <span>Plastic {score?.mass_balance?.plastic_kg_m3 ?? score?.plastic_diversion_kg_m3} kg</span>
          <span>Cost ₹{score?.mass_balance?.cost_inr_m3 ?? '—'}/m³</span>
          <span>CO₂e {score?.embodied_carbon_kgco2e_m3} kg</span>
          <span>{score?.pet_bottle_equiv} bottle equivalents</span>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="pb-3 border-b border-slate-200 mb-4">
          <h3 className="font-bold text-slate-950 text-base">Use-class gate</h3>
          <p className="text-xs font-semibold text-slate-700">
            A product is allowed only when its own standard clears on the lower confidence bound. Structural use stays a lab trial.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(score?.use_class_gates || []).map((gate) => (
            <div key={gate.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50">
              <div className="flex items-center justify-between gap-2">
                <span className="font-bold text-slate-950 text-sm">{gate.label}</span>
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                  gate.status === 'allowed' ? 'bg-emerald-100 text-emerald-900' :
                  gate.status === 'refused' ? 'bg-red-100 text-red-900' :
                  'bg-amber-100 text-amber-950'
                }`}>
                  {gate.status === 'verification_batch' ? 'Cast one verification batch' :
                   gate.status === 'lab_trial' ? 'Screen for a lab trial' :
                   gate.status === 'allowed' ? 'Allowed' : 'Refused'}
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-600 mt-1">{gate.standard}</p>
              <p className="text-xs text-slate-800 mt-2">{gate.message}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Prescriptive Remediation Advisor */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-700" />
            <h3 className="font-bold text-slate-950 text-base">
              Prescriptive Remediation Engine
            </h3>
          </div>
          <span className="text-xs font-mono font-bold text-emerald-800">
            From the use-class gate
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-100 border border-slate-200">
            <span className="font-bold text-emerald-800 block mb-1">Recommendation 1</span>
            <p className="text-slate-800 font-medium">
              {score?.remediation_action_1}
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-100 border border-slate-200">
            <span className="font-bold text-cyan-800 block mb-1">Recommendation 2</span>
            <p className="text-slate-800 font-medium">
              {score?.remediation_action_2}
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-100 border border-slate-200">
            <span className="font-bold text-indigo-800 block mb-1">Recommendation 3</span>
            <p className="text-slate-800 font-medium">
              {score?.remediation_action_3}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
