import React from 'react';
import { useMix } from '../context/MixContext';
import { GaugeChart } from '../components/GaugeChart';
import { evaluateUseClasses, type GateStatus } from '../lib/useClassGate';
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Info,
} from 'lucide-react';
import { TechnicalDetails } from '../components/TechnicalDetails';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

const GATE_LABEL: Record<GateStatus, string> = {
  allowed: 'Clears screening',
  verification_batch: 'Verification batch',
  lab_trial: 'Lab trial only',
  refused: 'Does not clear',
};

export const Sustainability: React.FC = () => {
  const { score, prediction, activeMix, setMainRoute } = useMix();
  const balance = score?.mass_balance;
  const baseline = balance?.baseline_co2_kgco2e_m3;
  const currentCo2 = score?.embodied_carbon_kgco2e_m3;
  const co2Savings = baseline != null && currentCo2 != null ? baseline - currentCo2 : null;
  const co2SavingPct = score?.co2_saving_pct;

  const carbonRows = (balance?.rows ?? [])
    .filter((row) => row.material !== 'Batching overhead')
    .map((row) => ({ name: row.material, co2: row.co2_kgco2e_m3 }));

  const gates = score?.use_class_gates?.length
    ? score.use_class_gates
    : prediction
      ? evaluateUseClasses(
          Object.fromEntries(Object.entries(prediction.predictions).map(([key, value]) => [key, value.mean])),
          Object.fromEntries(Object.entries(prediction.predictions).map(([key, value]) => [key, value.ci_90_low])),
          Object.fromEntries(Object.entries(prediction.predictions).map(([key, value]) => [key, value.ci_90_high])),
        )
      : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div>
            <h2 className="text-xl font-heading font-bold text-[#1E2022] tracking-tight">
              Environmental impact and requirements
            </h2>
            <p className="text-xs text-[#525866] mt-1 max-w-2xl leading-relaxed">
              Estimated carbon and plastic mass for this mix, then screening against selected Indian Standard use-class limits. A clear screen is not certification.
            </p>
          </div>
        </div>

        <button
          onClick={() => setMainRoute('standards')}
          className="text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:underline flex items-center gap-1"
        >
          <span>Open requirements</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Top 3 KPI Cards: Sustainability Gauge, Cradle-to-Gate Carbon, Landfill Diversion */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Score Gauge Card */}
        <div className="engineering-card rounded-xl p-5 flex flex-col items-center justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="w-full pb-2 border-b border-[#E5E5E0] text-center">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Environmental score</span>
          </div>
          {score?.sustainability_score == null ? (
            <p className="py-8 text-xs text-[#525866]">The environmental score appears after the mix is scored.</p>
          ) : (
            <GaugeChart
              value={score.sustainability_score}
              grade={score.sustainability_grade}
              label="Environmental score"
              sublabel="Carbon, plastic mass, and screening gates."
              size={170}
            />
          )}
          <div className="w-full pt-3 border-t border-[#E5E5E0] text-center text-[11px] text-[#525866] font-mono">
            Grade {score?.sustainability_grade || '—'}
            {score?.igbc_total_credits != null ? ` · IGBC ${score.igbc_total_credits} credits` : ''}
          </div>
        </div>

        {/* Embodied Carbon Accounting */}
        <div className="engineering-card rounded-xl p-5 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Estimated embodied carbon</span>
            <span className="text-xs font-mono font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
              {co2SavingPct != null ? `${co2SavingPct.toFixed(1)}% vs baseline` : 'Awaiting score'}
            </span>
          </div>

          <div className="space-y-4 my-auto py-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#1E2022] font-semibold">Plastic Composite Mix:</span>
                <span className="font-mono font-bold text-[#2563EB]">
                  {currentCo2 != null ? `${currentCo2.toFixed(1)} kg CO₂e/m³` : '—'}
                </span>
              </div>
              <div className="w-full h-2.5 bg-[#E5E5E0] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#2563EB] rounded-full transition-all"
                  style={{ width: baseline && currentCo2 != null ? `${Math.min(100, (currentCo2 / baseline) * 100)}%` : '0%' }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#1E2022] font-semibold">Conventional M20 Baseline:</span>
                <span className="font-mono font-bold text-[#525866]">
                  {baseline != null ? `${baseline.toFixed(1)} kg CO₂e/m³` : '—'}
                </span>
              </div>
              <div className="w-full h-2.5 bg-[#E5E5E0] rounded-full overflow-hidden">
                <div className="h-full bg-[#333A42] rounded-full w-full" />
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0] text-xs font-mono flex items-center justify-between text-[#1E2022]">
              <span>Difference vs baseline:</span>
              <span className="font-bold">
                {co2Savings != null ? `${co2Savings >= 0 ? '−' : '+'}${Math.abs(co2Savings).toFixed(1)} kg CO₂e/m³` : '—'}
              </span>
            </div>
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] text-[11px] text-[#525866]">
            Cradle-to-gate estimate using the configured ICE v4.1 factor table. Scope and assumptions are in technical details.
          </div>
        </div>

        {/* Plastic Diversion & Mass Accounting */}
        <div className="engineering-card rounded-xl p-5 flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
            <span className="eyebrow-tag text-[10px] text-[#525866]">Plastic waste in this mix</span>
          </div>

          <div className="my-auto py-2 space-y-3">
            <div>
            <span className="text-3xl font-bold font-mono text-[#1E2022]">
              {score?.plastic_diversion_kg_m3 != null ? score.plastic_diversion_kg_m3.toFixed(1) : '—'}
            </span>
              <span className="text-xs font-semibold text-[#525866] font-mono ml-1">kg plastic / m³</span>
            </div>
            <p className="text-xs text-[#525866] leading-relaxed">
              Mass of shredded {activeMix.plastic_type} replacing natural aggregate in one cubic metre of this mix.
            </p>
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] flex justify-between text-xs font-mono">
            <span className="text-[#525866]">PET Bottle Equiv:</span>
            <span className="font-bold text-[#1E2022]">
              {score?.pet_bottle_equiv != null ? `${score.pet_bottle_equiv} bottles` : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Visual Analytics 2-Grid: Carbon Contribution Stack (Left) & Standards Checklist (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Stacked Carbon Breakdown Bar Chart (7 cols) */}
        <div className="lg:col-span-7 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
            <div>
              <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                Carbon by material (kg CO₂e / m³)
              </h3>
              <p className="text-xs text-[#525866]">
                Share of estimated embodied carbon from each constituent, using the configured factor table.
              </p>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            {carbonRows.length === 0 ? (
              <div className="h-full flex items-center justify-center text-center text-xs text-[#525866] px-6">
                Carbon by material appears after the sustainability calculation returns a mass-balance ledger.
              </div>
            ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={carbonRows}
                layout="vertical"
                margin={{ top: 10, right: 24, left: 8, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" horizontal={false} />
                <XAxis type="number" stroke="#525866" fontSize={11} tickLine={false} unit=" kg" />
                <YAxis type="category" dataKey="name" stroke="#525866" fontSize={11} tickLine={false} width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#333A42',
                    borderColor: '#282E34',
                    borderRadius: '8px',
                    color: '#FFFFFF',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                  formatter={(val) => [`${val} kg CO₂e/m³`, 'Embodied carbon']}
                />
                <Bar dataKey="co2" fill="#2563EB" radius={[0, 4, 4, 0]} name="kg CO₂e/m³" />
              </BarChart>
            </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Right: Use-Class Compliance Gates (5 cols) */}
        <div className="lg:col-span-5 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
              <div>
                <h3 className="font-heading font-bold text-[#1E2022] text-sm">
                  Requirement screening
                </h3>
                <p className="text-xs text-[#525866]">Checks actually run against the selected use-class limits. Unknown checks are marked, not assumed to pass.</p>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              {gates.length === 0 ? (
                <p className="text-[#525866]">Screening results appear after a property prediction is available. A clear result is not a certificate.</p>
              ) : gates.map((gate) => (
                <div key={gate.id} className="p-3 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] flex items-start justify-between gap-3">
                  <div>
                    <span className="font-mono font-bold text-[#1E2022] block">{gate.standard}</span>
                    <span className="text-[11px] text-[#525866] block">{gate.label}</span>
                    {gate.clause ? <span className="text-[10px] font-mono text-[#525866] block">Criterion used: {gate.clause}</span> : null}
                    <span className="text-[11px] text-[#525866]">{gate.message}</span>
                  </div>
                  <span className={`shrink-0 inline-flex items-center gap-1 font-mono font-bold px-2 py-0.5 rounded text-[10px] border ${
                    gate.status === 'allowed'
                      ? 'text-[#1E2022] bg-white border-[#E5E5E0]'
                      : gate.status === 'refused'
                      ? 'text-[#9A3412] bg-[#FFF7ED] border-[#F97316]/30'
                      : 'text-[#333A42] bg-white border-[#E5E5E0]'
                  }`}>
                    {gate.status === 'refused' ? <AlertTriangle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                    {GATE_LABEL[gate.status]}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] mt-3 flex items-center gap-2 text-xs text-[#525866]">
            <Info className="w-3.5 h-3.5 text-[#2563EB] shrink-0" />
            <span>Meeting a selected screening criterion is not formal compliance, certification, or laboratory approval.</span>
          </div>
        </div>
      </div>

      <TechnicalDetails>
        <p>Carbon is a cradle-to-gate estimate from the shared mass-balance ledger and ICE Database v4.1 emission factors configured in this project. It is not a verified environmental product declaration.</p>
        <p>Use-class gates compare predicted compressive strength, water absorption, and density (where configured) with the limits in the gate table. Checks that were not run stay unmarked. IGBC / GRIHA / LEED figures are displayed only when the scoring service returns them.</p>
      </TechnicalDetails>
    </div>
  );
};
