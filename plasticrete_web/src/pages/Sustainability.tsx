import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { GaugeChart } from '../components/GaugeChart';
import {
  ShieldCheck,
  Award,
  Sparkles,
  TrendingDown,
  CheckCircle,
  XCircle,
} from 'lucide-react';

export const Sustainability: React.FC = () => {
  const { score, prediction } = useMix();

  const cs = prediction?.predictions.compressive_strength_mpa?.mean || 0;
  const density = prediction?.predictions.density_kgm3?.mean || 0;
  const waterAbs = prediction?.predictions.water_absorption_pct?.mean || 0;

  // BIS Standards Checks
  const is1237Pass = cs >= 30.0 && waterAbs <= 10.0;
  const is2185Pass = cs >= 5.0 && density >= 1800.0;
  const is456Pass = cs >= 20.0;

  return (
    <div className="space-y-6">
      <MixControlPanel />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">
            M3 Sustainability, LCA & BIS Compliance Engine
          </h2>
          <p className="text-xs font-semibold text-slate-700">
            Life cycle embodied carbon accounting (ICE 3.0), Bureau of Indian Standards checking & green building credits
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
          <GaugeChart
            value={score?.sustainability_score || 0}
            grade={score?.sustainability_grade || 'B'}
            label="PlastiCrete Green Rating"
            sublabel="Target: Grade A+ (>=85)"
            size={180}
          />
          <div className="w-full pt-3 border-t border-slate-200 text-center text-xs font-semibold text-slate-700">
            Weighted across 5 lifecycle criteria
          </div>
        </div>

        {/* Embodied Carbon Accounting */}
        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Embodied Carbon (Cradle-to-Gate)</span>
            <span className="text-xs font-mono font-bold text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300">
              -{score?.co2_saving_pct}% Saved
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
                  style={{ width: `${Math.min(100, ((score?.embodied_carbon_kgco2e_m3 || 280) / 365.7) * 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-900 font-bold">Conventional M20 Baseline:</span>
                <span className="font-mono font-bold text-slate-700">365.71 kg CO₂e/m³</span>
              </div>
              <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-slate-500 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 flex items-center gap-2 text-xs font-semibold text-slate-800">
            <TrendingDown className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>Net saving: {Math.max(0, 365.71 - (score?.embodied_carbon_kgco2e_m3 || 280)).toFixed(1)} kg CO₂e per cubic meter</span>
          </div>
        </div>

        {/* Circular Economy & Green Credits */}
        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Green Rating Points</span>
            <div className="p-1 rounded bg-amber-100 text-amber-900">
              <Award className="w-4 h-4" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center my-auto py-2">
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">IGBC Green</span>
              <span className="text-xl font-extrabold font-mono text-emerald-800">
                {score?.igbc_total_credits}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">credits</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">GRIHA v2019</span>
              <span className="text-xl font-extrabold font-mono text-cyan-800">
                {score?.griha_material_criterion_pts}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">points</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">LEED v4.1</span>
              <span className="text-xl font-extrabold font-mono text-indigo-800">
                {score?.leed_total_points}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">points</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 flex items-center justify-between text-xs">
            <span className="font-bold text-slate-800">PET Bottle Equiv:</span>
            <span className="font-mono font-extrabold text-slate-950">
              ≈ {(score?.pet_bottle_equiv || 0).toLocaleString()} bottles/m³
            </span>
          </div>
        </div>
      </div>

      {/* BIS Compliance Matrix */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
          <div>
            <h3 className="font-bold text-slate-950 text-base">
              Bureau of Indian Standards (BIS) Code Verification
            </h3>
            <p className="text-xs font-semibold text-slate-700">
              Structural and non-structural threshold compliance check
            </p>
          </div>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
            score?.bis_overall_pass
              ? 'bg-emerald-100 text-emerald-950 border border-emerald-300'
              : 'bg-amber-100 text-amber-950 border border-amber-300'
          }`}>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Overall BIS Verdict: {score?.bis_overall_pass ? 'APPROVED' : 'MARGINAL'}</span>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-300 text-slate-800 font-bold font-mono">
                <th className="pb-2 font-bold text-slate-900">Standard Code</th>
                <th className="pb-2 font-bold text-slate-900">Description</th>
                <th className="pb-2 font-bold text-slate-900">Primary Requirement</th>
                <th className="pb-2 font-bold text-slate-900">Current Mix Value</th>
                <th className="pb-2 font-bold text-slate-900 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              <tr>
                <td className="py-2.5 font-bold font-mono text-slate-950">IS 1237:2012</td>
                <td className="py-2.5 font-medium text-slate-800">Cement Concrete Flooring & Paving Tiles</td>
                <td className="py-2.5 font-mono font-semibold text-slate-800">CS &gt;= 30 MPa, Water Abs &lt;= 10%</td>
                <td className="py-2.5 font-mono font-bold text-slate-950">{cs} MPa / {waterAbs}%</td>
                <td className="py-2.5 text-right">
                  <span className={`inline-flex items-center gap-1 font-bold ${is1237Pass ? 'text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded' : 'text-amber-900 bg-amber-100 px-2 py-0.5 rounded'}`}>
                    {is1237Pass ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    {is1237Pass ? 'Pass' : 'Low CS'}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold font-mono text-slate-950">IS 2185 (Part 1)</td>
                <td className="py-2.5 font-medium text-slate-800">Concrete Masonry Blocks (Load-bearing)</td>
                <td className="py-2.5 font-mono font-semibold text-slate-800">CS &gt;= 5.0 MPa, Density &gt;= 1800 kg/m³</td>
                <td className="py-2.5 font-mono font-bold text-slate-950">{cs} MPa / {density} kg/m³</td>
                <td className="py-2.5 text-right">
                  <span className={`inline-flex items-center gap-1 font-bold ${is2185Pass ? 'text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded' : 'text-amber-900 bg-amber-100 px-2 py-0.5 rounded'}`}>
                    {is2185Pass ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    {is2185Pass ? 'Pass' : 'Density fail'}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold font-mono text-slate-950">IS 456:2000</td>
                <td className="py-2.5 font-medium text-slate-800">Plain & Reinforced Structural Concrete</td>
                <td className="py-2.5 font-mono font-semibold text-slate-800">Minimum M20 grade (CS &gt;= 20.0 MPa)</td>
                <td className="py-2.5 font-mono font-bold text-slate-950">{cs} MPa</td>
                <td className="py-2.5 text-right">
                  <span className={`inline-flex items-center gap-1 font-bold ${is456Pass ? 'text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded' : 'text-amber-900 bg-amber-100 px-2 py-0.5 rounded'}`}>
                    {is456Pass ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    {is456Pass ? 'Pass' : 'Under M20'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
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
            Potential Score Uplift: +{score?.estimated_score_gain || 0} pts
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
