import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import { OperationProgress } from '../components/OperationProgress';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { TARGET_LABELS } from '../types';
import {
  ChevronDown,
  Target,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Info,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface BenchmarkSpec {
  name: string;
  code: string;
  targets: Record<string, number>;
}

const BENCHMARKS: BenchmarkSpec[] = [
  {
    name: 'M20 general construction / pavers',
    code: 'IS 456 / IS 15658 comparison',
    targets: {
      compressive_strength_mpa: 20.0,
      flexural_strength_mpa: 2.8,
      split_tensile_mpa: 1.8,
      density_kgm3: 2200,
      water_absorption_pct: 5.0,
      thermal_conductivity_wm: 1.3,
      durability_index: 45.0,
    },
  },
  {
    name: 'M25 heavy-duty paving',
    code: 'IS 15658 M25 comparison',
    targets: {
      compressive_strength_mpa: 25.0,
      flexural_strength_mpa: 3.5,
      split_tensile_mpa: 2.4,
      density_kgm3: 2250,
      water_absorption_pct: 4.5,
      thermal_conductivity_wm: 1.4,
      durability_index: 55.0,
    },
  },
  {
    name: 'M15 masonry / partition units',
    code: 'IS 2185 Part 1 comparison',
    targets: {
      compressive_strength_mpa: 15.0,
      flexural_strength_mpa: 2.0,
      split_tensile_mpa: 1.4,
      density_kgm3: 2100,
      water_absorption_pct: 7.0,
      thermal_conductivity_wm: 1.1,
      durability_index: 35.0,
    },
  },
];

function shown(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
}

function meetsComparison(key: string, mean: number, target: number): boolean {
  if (key === 'water_absorption_pct' || key === 'thermal_conductivity_wm') {
    return mean <= target;
  }
  return mean >= target;
}

export const Predictor: React.FC = () => {
  const {
    prediction,
    applyPreset,
    loading,
    refreshAll,
    operationStatus,
    operationStartTime,
    cancelOperation,
    setIsDrawerOpen,
    setStudioTab,
  } = useMix();

  const [selectedBenchmarkIdx, setSelectedBenchmarkIdx] = useState<number>(0);
  const activeBenchmark = BENCHMARKS[selectedBenchmarkIdx];

  const rows = Object.entries(TARGET_LABELS).map(([key, meta]) => {
    const result = prediction?.predictions[key];
    const mean = result?.mean ?? null;
    const targetVal = activeBenchmark.targets[key];
    const isWaterOrThermal = key === 'water_absorption_pct' || key === 'thermal_conductivity_wm';
    const isMet =
      mean != null && targetVal != null ? meetsComparison(key, mean, targetVal) : null;
    return {
      key,
      label: meta.label,
      unit: meta.unit,
      description: meta.description,
      mean,
      low: result?.ci_90_low ?? null,
      high: result?.ci_90_high ?? null,
      target: targetVal ?? null,
      isMet,
      needsAttention: isMet === false,
      lowerIsBetter: isWaterOrThermal,
    };
  });

  const predictedCount = rows.filter((row) => row.mean != null).length;
  const attention = rows.filter((row) => row.needsAttention);
  const chartRows = rows
    .filter((row) => row.mean != null && row.target != null && row.target > 0)
    .map((row) => ({
      label: row.label,
      unit: row.unit,
      predicted: Number(row.mean!.toFixed(2)),
      target: row.target,
      pctOfTarget: Number(((row.mean! / row.target!) * 100).toFixed(1)),
      isMet: row.isMet === true,
    }));

  return (
    <div className="space-y-6">
      <div className="engineering-card rounded-xl p-4 bg-[#FFFFFF] border border-[#E5E5E0] shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-heading font-bold text-[#1E2022] tracking-tight">
            Predicted concrete performance
          </h2>
          <p className="text-xs text-[#525866] mt-1 max-w-2xl leading-relaxed">
            These are model estimates for the current mix, not laboratory cube results. Units sit beside each value. A prediction range is shown only when the service returned one.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative min-w-[240px]">
            <select
              onChange={(e) => applyPreset(e.target.value)}
              className="w-full text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] text-[#1E2022] pl-3 pr-8 py-2 focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer appearance-none shadow-xs"
              defaultValue=""
            >
              <option value="" disabled>Load a starting mix…</option>
              {['M20 Eco-Standard (PET 15%)', 'High-Duty Paving (HDPE 20%)', 'Ultra-Green Diversion (Mixed 25%)', 'Lightweight Partition (LDPE 30%)'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#525866] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="px-3 py-2 text-xs font-semibold rounded-lg bg-[#333A42] hover:bg-[#282E34] text-white transition-colors cursor-pointer shadow-xs whitespace-nowrap"
          >
            Define your mix
          </button>
        </div>
      </div>

      {(loading || operationStatus === 'error' || operationStatus === 'timeout') && (
        <OperationProgress
          title={
            loading
              ? 'Preparing your prediction…'
              : operationStatus === 'timeout'
              ? 'The prediction timed out'
              : 'The prediction could not be completed'
          }
          description={
            loading
              ? 'Estimating seven concrete properties for this mix. Typical waits are a few seconds.'
              : 'The prediction service is temporarily unavailable. Your saved mix is unchanged. Try again or review the inputs.'
          }
          status={loading ? operationStatus : operationStatus}
          startTime={operationStartTime}
          expectedDurationMs={3500}
          onRetry={refreshAll}
          onCancel={loading ? cancelOperation : undefined}
        />
      )}

      {!loading && prediction && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="engineering-card rounded-xl p-4 border border-[#E5E5E0] bg-[#FFFFFF]">
            <span className="eyebrow-tag text-[10px] text-[#525866] block">Predicted properties</span>
            <p className="text-2xl font-mono font-bold text-[#1E2022] mt-1">{predictedCount} of 7</p>
            <p className="text-[11px] text-[#525866] mt-1">Values with units. Missing results show as unavailable.</p>
          </div>
          <div className="engineering-card rounded-xl p-4 border border-[#E5E5E0] bg-[#FFFFFF]">
            <span className="eyebrow-tag text-[10px] text-[#525866] block">Compared with</span>
            <p className="text-sm font-heading font-bold text-[#1E2022] mt-1">{activeBenchmark.name}</p>
            <p className="text-[11px] text-[#525866] mt-1">{activeBenchmark.code}. Screening comparison only.</p>
          </div>
          <div className="engineering-card rounded-xl p-4 border border-[#E5E5E0] bg-[#FFFFFF]">
            <span className="eyebrow-tag text-[10px] text-[#525866] block">Needs attention</span>
            <p className="text-2xl font-mono font-bold text-[#1E2022] mt-1">{attention.length}</p>
            <p className="text-[11px] text-[#525866] mt-1">
              {attention.length === 0
                ? 'No predicted property sits on the wrong side of the selected comparison.'
                : attention.map((row) => row.label).join(', ')}
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Target className="w-3.5 h-3.5 text-[#2563EB]" />
          <span className="text-xs font-semibold text-[#525866]">Compare with this grade</span>
        </div>
        <select
          value={selectedBenchmarkIdx}
          onChange={(e) => setSelectedBenchmarkIdx(Number(e.target.value))}
          className="text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] text-[#1E2022] px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer shadow-xs"
        >
          {BENCHMARKS.map((b, idx) => (
            <option key={b.name} value={idx}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs overflow-x-auto">
        <h3 className="font-heading font-bold text-sm text-[#1E2022] mb-1">Property comparison</h3>
        <p className="text-xs text-[#525866] mb-4">
          Predicted mean versus the comparison values on this screen. Water absorption and thermal conductivity are better when lower.
        </p>
        <table className="w-full text-xs text-left min-w-[640px]">
          <thead>
            <tr className="border-b border-[#E5E5E0] text-[#525866] font-mono text-[10px] uppercase">
              <th className="py-2 pr-3">Property</th>
              <th className="py-2 px-3 text-right">Predicted</th>
              <th className="py-2 px-3 text-right">Unit</th>
              <th className="py-2 px-3 text-right">Prediction range</th>
              <th className="py-2 px-3 text-right">Comparison</th>
              <th className="py-2 pl-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E5E0]">
            {rows.map((row) => (
              <tr key={row.key} className={row.needsAttention ? 'bg-[#FFF7ED]/60' : ''}>
                <td className="py-2.5 pr-3 font-medium text-[#1E2022]">{row.label}</td>
                <td className="py-2.5 px-3 text-right font-mono font-bold text-[#1E2022]">{shown(row.mean)}</td>
                <td className="py-2.5 px-3 text-right font-mono text-[#525866]">{row.unit}</td>
                <td className="py-2.5 px-3 text-right font-mono text-[#2563EB]">
                  {row.low != null && row.high != null ? `${shown(row.low)} – ${shown(row.high)}` : 'Unavailable'}
                </td>
                <td className="py-2.5 px-3 text-right font-mono text-[#525866]">
                  {row.target != null ? `${row.lowerIsBetter ? '≤' : '≥'} ${shown(row.target, 1)}` : '—'}
                </td>
                <td className="py-2.5 pl-3 text-right">
                  {row.mean == null ? (
                    <span className="text-[#525866]">Unavailable</span>
                  ) : row.isMet ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Meets comparison
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[#9A3412]">
                      <AlertTriangle className="w-3.5 h-3.5" /> Needs attention
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {chartRows.length > 0 && (
        <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <h3 className="font-heading font-bold text-sm text-[#1E2022]">Predicted value as a share of the comparison</h3>
          <p className="text-xs text-[#525866] mb-3">
            100% equals the selected comparison value. This is a screening chart, not a laboratory result.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartRows} layout="vertical" margin={{ top: 10, right: 30, left: 110, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" horizontal={false} />
                <XAxis type="number" stroke="#525866" fontSize={11} tickLine={false} unit="%" domain={[0, 150]} />
                <YAxis type="category" dataKey="label" stroke="#525866" fontSize={11} tickLine={false} width={110} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#333A42', borderColor: '#282E34', borderRadius: '8px', color: '#FFFFFF', fontSize: '11px' }}
                  formatter={(_val, _name, item: { payload?: { predicted: number; unit: string; target: number; pctOfTarget: number; isMet: boolean } }) => [
                    `${item.payload?.predicted} ${item.payload?.unit} (comparison ${item.payload?.target} ${item.payload?.unit}, ${item.payload?.pctOfTarget}%)`,
                    item.payload?.isMet ? 'Meets comparison' : 'Needs attention',
                  ]}
                />
                <Bar dataKey="pctOfTarget" radius={[0, 4, 4, 0]}>
                  {chartRows.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.isMet ? '#2563EB' : '#F97316'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
        <h3 className="font-heading font-bold text-sm text-[#1E2022] mb-2">What you can do next</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setStudioTab('explainability')}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] hover:bg-[#E5E5E0] text-xs font-semibold text-[#1E2022] cursor-pointer"
          >
            Why this prediction <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setStudioTab('optimizer')}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] hover:bg-[#E5E5E0] text-xs font-semibold text-[#1E2022] cursor-pointer"
          >
            Improve your mix <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setStudioTab('sustainability')}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] hover:bg-[#E5E5E0] text-xs font-semibold text-[#1E2022] cursor-pointer"
          >
            Environmental impact <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] p-4 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-[#2563EB] shrink-0 mt-0.5" />
        <div className="text-xs text-[#525866] leading-relaxed">
          <strong className="text-[#1E2022]">Assumptions and limits.</strong> Predictions are statistical screening estimates. The comparison values on this page are typical grade floors for the selected use, not a certificate. Physical cube testing to IS 516 is required before production.
          {prediction?.uncertainty_flag ? ' This mix is flagged as outside the denser part of the training data, so the prediction range may be wide.' : ''}
          {prediction?.low_coverage_targets?.length ? ` Low coverage: ${prediction.low_coverage_targets.join(', ')}.` : ''}
        </div>
      </div>

      <TechnicalDetails>
        <p>Property prediction uses the existing ensemble pipeline (XGBoost, Random Forest, and a neural network). The prediction range is the empirical 90% interval returned by that service.</p>
        <p>Comparison values on this screen are user-selected grade floors. They are not substituted for missing model outputs. Unavailable means the service did not return that field.</p>
      </TechnicalDetails>
    </div>
  );
};
