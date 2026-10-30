import React, { useState, useEffect, useTransition } from 'react';
import { useMix } from '../context/MixContext';
import { predictProperties } from '../api/client';
import { computeMassBalance } from '../lib/massBalance';
import { OperationProgress } from '../components/OperationProgress';
import type { MixInput, PredictionResponse } from '../types';
import {
  Sliders,
  RotateCcw,
  ArrowRight,
  ChevronRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const PLASTIC_OPTIONS = [
  { value: 'PET', label: 'Polyethylene Terephthalate (PET Flakes)' },
  { value: 'HDPE', label: 'High-Density Polyethylene (HDPE Pellets)' },
  { value: 'LDPE', label: 'Low-Density Polyethylene (LDPE Shreds)' },
  { value: 'PP', label: 'Polypropylene (PP Fibers/Granules)' },
  { value: 'PVC', label: 'Polyvinyl Chloride (PVC Regrind)' },
];

const ADDITIVE_OPTIONS = [
  { value: 'fly_ash', label: 'Class F Fly Ash (IS 3812)' },
  { value: 'silica_fume', label: 'Silica Fume / Microsilica (ASTM C1240)' },
  { value: 'ggbs', label: 'Ground Granulated Blast Furnace Slag (GGBS)' },
  { value: 'metakaolin', label: 'High-Reactivity Metakaolin' },
  { value: 'nano_silica', label: 'Colloidal Nano-Silica Solution' },
  { value: 'none', label: 'No SCM Additive (Control)' },
];

export const InteractivePage: React.FC = () => {
  const { mix: sharedMix, setMix: setSharedMix, setMainRoute, setStudioTab } = useMix();

  // Local interactive simulator state initialized from shared mix
  const [localMix, setLocalMix] = useState<MixInput>(sharedMix);
  const [livePrediction, setLivePrediction] = useState<PredictionResponse | null>(null);
  const [controlPrediction, setControlPrediction] = useState<PredictionResponse | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);
  const [, startTransition] = useTransition();

  // Run live prediction whenever localMix changes (debounced by 300ms)
  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      setSimLoading(true);
      setSimError(null);

      try {
        // Query live model prediction for composite mix
        const pred = await predictProperties(localMix);
        if (cancelled) return;
        setLivePrediction(pred);

        // Also query control baseline (0% plastic, same w/c and curing) if not cached
        if (!controlPrediction || controlPrediction.predictions.compressive_strength_mpa == null) {
          const controlMix: MixInput = {
            ...localMix,
            replacement_pct: 0,
            plastic_type: 'PET',
          };
          const ctrl = await predictProperties(controlMix);
          if (!cancelled) setControlPrediction(ctrl);
        }
      } catch (err: unknown) {
        if (cancelled) return;
        setSimError(err instanceof Error ? err.message : 'The prediction service is temporarily unavailable. Your saved mix is unchanged.');
      } finally {
        if (!cancelled) setSimLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [localMix]);

  const updateParam = <K extends keyof MixInput>(key: K, val: MixInput[K]) => {
    startTransition(() => {
      setLocalMix((prev) => ({ ...prev, [key]: val }));
    });
  };

  const handlePromoteToStudio = () => {
    setSharedMix(localMix);
    setMainRoute('studio');
    setStudioTab('overview');
  };

  const handleReset = () => {
    setLocalMix(sharedMix);
  };

  // Comparative chart data between Plastic Composite and Control Concrete
  const compStrength = livePrediction?.predictions?.compressive_strength_mpa?.mean;
  const ctrlStrength = controlPrediction?.predictions?.compressive_strength_mpa?.mean;
  const flexStrength = livePrediction?.predictions?.flexural_strength_mpa?.mean;
  const ctrlFlex = controlPrediction?.predictions?.flexural_strength_mpa?.mean;
  const density = livePrediction?.predictions?.density_kgm3?.mean;
  const thermal = livePrediction?.predictions?.thermal_conductivity_wm?.mean;
  const divertedKg = computeMassBalance(localMix).plastic_kg_m3;

  const comparisonData = [
    {
      name: 'Compressive (MPa)',
      Composite: compStrength != null ? Number(compStrength.toFixed(1)) : null,
      Control: ctrlStrength != null ? Number(ctrlStrength.toFixed(1)) : null,
    },
    {
      name: 'Flexural (MPa)',
      Composite: flexStrength != null ? Number(flexStrength.toFixed(1)) : null,
      Control: ctrlFlex != null ? Number(ctrlFlex.toFixed(1)) : null,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Breadcrumb & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E0]">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#525866] mb-1">
            <button
              onClick={() => setMainRoute('home')}
              className="hover:text-[#1E2022] transition-colors cursor-pointer"
            >
              Home
            </button>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-[#1E2022] font-bold">Mix simulator</span>
          </div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-heading font-bold text-[#1E2022] tracking-tight">
              Mix simulator
            </h1>
          </div>
          <p className="text-xs text-[#525866] mt-1">
            Change mix proportions and see the predicted properties update. Values are model estimates, not laboratory measurements.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-xs font-semibold text-[#333A42] transition-colors cursor-pointer shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#525866]" />
            <span>Reset to Shared Mix</span>
          </button>

          <button
            onClick={handlePromoteToStudio}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-all cursor-pointer shadow-xs"
          >
            <span>Use this mix in the workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Simulator Notice / Status */}
      {simError && (
        <OperationProgress
          title="The prediction could not be completed"
          description={simError}
          status="error"
          onRetry={() => updateParam('replacement_pct', localMix.replacement_pct)}
        />
      )}

      {/* 2-Column Split: Controls (Left) and Live Physical Output (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Parametric Sliders (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#2563EB]" />
                <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                  Physical Batch Proportions
                </h3>
              </div>
              <span className="eyebrow-tag text-[9px] text-[#525866]">IS 10262</span>
            </div>

            <div className="space-y-4 text-xs">
              {/* Polymer Type Select */}
              <div>
                <label className="block text-[11px] font-semibold text-[#1E2022] mb-1.5">
                  Polymer Aggregate Type
                </label>
                <select
                  value={localMix.plastic_type}
                  onChange={(e) => updateParam('plastic_type', e.target.value)}
                  className="w-full text-xs font-medium rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
                >
                  {PLASTIC_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Plastic Replacement Slider */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Plastic Replacement (%)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{localMix.replacement_pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="40"
                  step="1"
                  value={localMix.replacement_pct}
                  onChange={(e) => updateParam('replacement_pct', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] font-mono text-[#525866] mt-0.5">
                  <span>0% (Control)</span>
                  <span>20% (Optimal)</span>
                  <span>40% (Max)</span>
                </div>
              </div>

              {/* Water / Cement Ratio Slider */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Water / Cement Ratio (w/c)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{localMix.wc_ratio.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.35"
                  max="0.65"
                  step="0.01"
                  value={localMix.wc_ratio}
                  onChange={(e) => updateParam('wc_ratio', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] font-mono text-[#525866] mt-0.5">
                  <span>0.35 (Dry/High Strength)</span>
                  <span>0.50 (Standard)</span>
                  <span>0.65 (High Porosity)</span>
                </div>
              </div>

              {/* Particle Gradation Slider */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Plastic Particle Size (mm)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{localMix.particle_size_mm} mm</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="12"
                  step="0.5"
                  value={localMix.particle_size_mm}
                  onChange={(e) => updateParam('particle_size_mm', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] font-mono text-[#525866] mt-0.5">
                  <span>0.5 mm (Fine Sand)</span>
                  <span>4.0 mm (Coarse Sand)</span>
                  <span>12 mm (Gravel)</span>
                </div>
              </div>

              {/* SCM Additive Selector */}
              <div>
                <label className="block text-[11px] font-semibold text-[#1E2022] mb-1.5">
                  Supplementary Mineral Additive
                </label>
                <select
                  value={localMix.additive_type}
                  onChange={(e) => updateParam('additive_type', e.target.value)}
                  className="w-full text-xs font-medium rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
                >
                  {ADDITIVE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Additive Dosage Slider */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Additive Dosage (% Binder)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{localMix.additive_pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="30"
                  step="1"
                  value={localMix.additive_pct}
                  onChange={(e) => updateParam('additive_pct', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
              </div>

              {/* Curing Age & Temp Dual Sliders */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-[#1E2022]">Curing (Days)</span>
                    <span className="font-mono font-bold text-[#2563EB]">{localMix.curing_days}d</span>
                  </div>
                  <input
                    type="range"
                    min="3"
                    max="90"
                    step="1"
                    value={localMix.curing_days}
                    onChange={(e) => updateParam('curing_days', Number(e.target.value))}
                    className="w-full accent-[#2563EB] cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-[#1E2022]">Temp (°C)</span>
                    <span className="font-mono font-bold text-[#2563EB]">{localMix.curing_temp_c}°C</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="60"
                    step="1"
                    value={localMix.curing_temp_c}
                    onChange={(e) => updateParam('curing_temp_c', Number(e.target.value))}
                    className="w-full accent-[#2563EB] cursor-pointer"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Comparative Charts & Scientific Visuals (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Top Key Performance Metrics Card */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
              <span className="eyebrow-tag text-[9px] text-[#525866] block mb-1">Compressive</span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold font-mono text-[#1E2022]">
                  {compStrength != null ? compStrength.toFixed(1) : '—'}
                </span>
                <span className="text-[10px] text-[#525866] font-mono">MPa</span>
              </div>
              <span className="text-[10px] font-mono text-[#2563EB] mt-0.5 block">
                {compStrength != null && ctrlStrength ? `${((compStrength / ctrlStrength) * 100).toFixed(0)}% of 0% plastic control` : 'Predicted, not lab-tested'}
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
              <span className="eyebrow-tag text-[9px] text-[#525866] block mb-1">Bulk density</span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold font-mono text-[#2563EB]">
                  {density != null ? density.toFixed(0) : '—'}
                </span>
                <span className="text-[10px] text-[#525866] font-mono">kg/m³</span>
              </div>
              <span className="text-[10px] font-mono text-[#525866] mt-0.5 block">Predicted density</span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
              <span className="eyebrow-tag text-[9px] text-[#525866] block mb-1">Thermal conductivity</span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold font-mono text-[#1E2022]">
                  {thermal != null ? thermal.toFixed(2) : '—'}
                </span>
                <span className="text-[10px] text-[#525866] font-mono">W/m·K</span>
              </div>
              <span className="text-[10px] font-mono text-[#2563EB] mt-0.5 block">Lower conducts less heat</span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
              <span className="eyebrow-tag text-[9px] text-[#525866] block mb-1">Polymer in the mix</span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold font-mono text-[#1E2022]">
                  {divertedKg.toFixed(1)}
                </span>
                <span className="text-[10px] text-[#525866] font-mono">kg/m³</span>
              </div>
              <span className="text-[10px] font-mono text-[#525866] mt-0.5 block">From the mass-balance ledger</span>
            </div>
          </div>

          {/* Mechanical Strength Comparison Bar Chart */}
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <div>
                <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                  Plastic Composite vs Conventional Concrete (IS 456)
                </h3>
                <p className="text-xs text-[#525866]">
                  Predicted mechanical strengths compared against 0% plastic control batch.
                </p>
              </div>
              {simLoading && (
                <span className="text-[11px] font-mono text-[#2563EB]" role="status">
                  Predicting this mix…
                </span>
              )}
            </div>

            <div className="h-64 w-full pt-2">
              {!livePrediction ? (
                <div className="h-full flex items-center justify-center text-center text-xs text-[#525866] px-6" role="status">
                  {simLoading
                    ? 'The property model is running. This chart appears when the prediction returns, usually within a few seconds.'
                    : 'Adjust the mix to request a prediction. Bars compare this mix with a 0% plastic control from the same model.'}
                </div>
              ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" vertical={false} />
                  <XAxis dataKey="name" stroke="#525866" fontSize={11} tickLine={false} />
                  <YAxis stroke="#525866" fontSize={11} tickLine={false} unit=" MPa" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#333A42',
                      borderColor: '#282E34',
                      borderRadius: '8px',
                      color: '#FFFFFF',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="Composite" fill="#2563EB" radius={[4, 4, 0, 0]} name="PlastiCrete Formulation" />
                  <Bar dataKey="Control" fill="#333A42" radius={[4, 4, 0, 0]} name="IS 456 Plain Concrete" />
                </BarChart>
              </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
            <h3 className="font-heading font-bold text-sm text-[#1E2022]">
              Replacement sweep
            </h3>
            <p className="text-xs text-[#525866] mt-2 leading-relaxed">
              The model predicts one mix at a time. A curve from 0% to 40% replacement is not returned, so this page does not draw an estimated decay. Move the replacement slider to request a new prediction. The active replacement is {localMix.replacement_pct}%.
              {compStrength != null ? ` Current predicted compressive strength is ${compStrength.toFixed(1)} MPa.` : ''}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
