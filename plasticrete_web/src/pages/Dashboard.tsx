import React from 'react';
import { useMix } from '../context/MixContext';
import { GaugeChart } from '../components/GaugeChart';
import {
  Activity,
  Leaf,
  Boxes,
  AlertTriangle,
  ArrowRight,
  Scale,
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
      {/* Uncertainty Notice if flagged */}
      {prediction?.uncertainty_flag && (
        <div className="p-3.5 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 flex items-center gap-2.5 text-xs text-[#1E2022]">
          <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0" />
          <span>
            <strong>Extrapolation Notice:</strong> High plastic volume (&gt;30%) or extreme w/c ratio enters low-density training distribution. Confidence intervals have widened accordingly.
          </span>
        </div>
      )}

      {/* 4 Core KPIs Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Compressive Strength */}
        <div className="engineering-card rounded-xl p-4 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between text-[#525866] mb-2">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Compressive Strength</span>
            <div className="p-1.5 rounded-md bg-[#F5F5F3] text-[#2563EB] border border-[#E5E5E0]">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold font-mono text-[#1E2022]">
                {shown(compressive?.mean)}
              </span>
              <span className="text-xs font-semibold text-[#525866] font-mono">MPa</span>
            </div>
            <p className="text-xs font-mono text-[#525866] mt-1">
              Prediction range: [{shown(compressive?.ci_90_low)} – {shown(compressive?.ci_90_high)}]
            </p>
          </div>
          <button
            onClick={() => setStudioTab('optimizer')}
            className="mt-3 pt-2 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>Improve your mix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* KPI 2: Embodied Carbon Saved */}
        <div className="engineering-card rounded-xl p-4 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between text-[#525866] mb-2">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Embodied Carbon Saved</span>
            <div className="p-1.5 rounded-md bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0]">
              <Leaf className="w-4 h-4 text-[#2563EB]" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold font-mono text-[#2563EB]">
                {co2Saving != null ? `${shown(co2Saving, 1)}%` : '—'}
              </span>
            </div>
            <p className="text-xs font-mono text-[#525866] mt-1">
              ICE v4.1 Mass Balance
            </p>
          </div>
          <button
            onClick={() => setStudioTab('sustainability')}
            className="mt-3 pt-2 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>Environmental impact</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* KPI 3: Waste Diverted */}
        <div className="engineering-card rounded-xl p-4 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between text-[#525866] mb-2">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Plastic Diverted</span>
            <div className="p-1.5 rounded-md bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0]">
              <Scale className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold font-mono text-[#1E2022]">
                {shown(diversionKg, 1)}
              </span>
              <span className="text-xs font-semibold text-[#525866] font-mono">kg/m³</span>
            </div>
            <p className="text-xs font-mono text-[#525866] mt-1">
              Virgin aggregate replaced
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-[#E5E5E0] text-[11px] font-mono text-[#525866]">
            Target &gt; 15 kg/m³
          </div>
        </div>

        {/* KPI 4: Top Application */}
        <div className="engineering-card rounded-xl p-4 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between text-[#525866] mb-2">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Top Use Class</span>
            <div className="p-1.5 rounded-md bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0]">
              <Boxes className="w-4 h-4 text-[#2563EB]" />
            </div>
          </div>
          <div>
            <div className="text-base font-bold text-[#1E2022] line-clamp-1 font-heading">
              {primaryApp ? (APPLICATION_PRETTY_NAMES[primaryApp] || primaryApp) : 'Calculating...'}
            </div>
            <p className="text-xs font-mono text-[#2563EB] mt-1">
              {confidence != null ? `${confidence}% suggested-use match` : 'Application match not returned'}
            </p>
          </div>
          <button
            onClick={() => setStudioTab('recommender')}
            className="mt-3 pt-2 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 hover:gap-1.5 transition-all cursor-pointer"
          >
            <span>Explore applications</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Two Column Section: Multi-Target Radar / Overview & Sustainability Gate */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 7 Properties Summary Table (7 cols) */}
        <div className="lg:col-span-7 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
            <div>
              <h3 className="font-heading font-bold text-[#1E2022] text-sm">
                Predicted properties
              </h3>
              <p className="text-xs text-[#525866]">
                Model estimates with prediction range where the service returned one. These are not cube results.
              </p>
            </div>
            <button
              onClick={() => setStudioTab('predictor')}
              className="text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8]"
            >
              Expand All
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[#E5E5E0] text-[#525866] font-mono text-[10px] uppercase">
                  <th className="py-2 pr-3">Target Property</th>
                  <th className="py-2 px-3 text-right">Predicted Mean</th>
                  <th className="py-2 pl-3 text-right">Prediction range</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E0] font-mono">
                {prediction?.predictions &&
                  Object.entries(prediction.predictions).map(([key, res]) => {
                    const meta = TARGET_LABELS[key];
                    const label = typeof meta === 'string' ? meta : meta?.label || key;
                    const unit = typeof meta === 'object' && meta?.unit ? meta.unit : '';
                    return (
                      <tr key={key} className="hover:bg-[#F5F5F3] transition-colors">
                        <td className="py-2.5 pr-3 font-sans font-medium text-[#1E2022]">
                          {label}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-[#1E2022]">
                          {shown(res.mean)} {unit}
                        </td>
                        <td className="py-2.5 pl-3 text-right text-[#2563EB]">
                          {res.ci_90_low != null && res.ci_90_high != null
                            ? `[${shown(res.ci_90_low)} – ${shown(res.ci_90_high)}]`
                            : '—'}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Aggregate Sustainability Index & Quick Check (5 cols) */}
        <div className="lg:col-span-5 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
            <div>
              <h3 className="font-heading font-bold text-[#1E2022] text-sm">
                Environmental score
              </h3>
              <p className="text-xs text-[#525866]">Carbon, plastic mass, and screening gates for this mix.</p>
            </div>
            <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
              Grade {score?.sustainability_grade || '—'}
            </span>
          </div>

          <div className="py-4 flex justify-center">
            {score?.sustainability_score != null ? (
              <GaugeChart
                value={score.sustainability_score}
                grade={score.sustainability_grade}
                label="Environmental score"
                sublabel="Cradle-to-gate mass balance"
                size={160}
              />
            ) : (
              <p className="text-xs text-[#525866]">The environmental score appears after the mix is scored.</p>
            )}
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[#525866]">Embodied Carbon:</span>
              <span className="font-mono font-bold text-[#1E2022]">
                {shown(score?.embodied_carbon_kgco2e_m3)} kg CO₂e/m³
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#525866]">Plastic in this mix:</span>
              <span className="font-mono font-bold text-[#1E2022]">
                {shown(score?.plastic_diversion_kg_m3)} kg/m³
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
