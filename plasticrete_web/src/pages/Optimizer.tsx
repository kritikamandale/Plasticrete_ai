import React, { useEffect, useRef, useState } from 'react';
import { useMix } from '../context/MixContext';
import { runOptimization } from '../api/client';
import type { TradeoffPoint } from '../types';
import { OperationProgress, type OperationStatus } from '../components/OperationProgress';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import {
  Sparkles,
  ArrowRight,
  Check,
} from 'lucide-react';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { FieldHelp } from '../components/FieldHelp';

function CandidateTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload?: { id?: string; cost?: number; cs?: number; replacement?: number; co2?: number } }> }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;
  return (
    <div className="rounded-lg border border-[#282E34] bg-[#333A42] px-3 py-2 text-[11px] font-mono text-white shadow-md">
      <p className="font-bold text-white">{point.id}</p>
      <p className="text-white">{Number(point.cs).toFixed(1)} MPa predicted strength</p>
      <p className="text-white">₹{Number(point.cost).toFixed(0)} / m³ estimated cost</p>
      <p className="text-white">{point.replacement}% plastic replacement · {Number(point.co2).toFixed(0)} kg CO₂/m³</p>
    </div>
  );
}

export const Optimizer: React.FC = () => {
  const {
    selectedCandidate,
    selectCandidate,
    optimizationResult,
    setOptimizationResult,
    cancelOperation,
  } = useMix();

  // Boundary Constraints initialized from active baseline mix
  const [repMax, setRepMax] = useState<number>(30.0);
  const [csMin, setCsMin] = useState<number>(20.0);
  const [plasticType, setPlasticType] = useState<string>('Any');

  // Weights (normalized to sum to 1.0)
  const [wCS, setWCS] = useState<number>(0.40);
  const [wCost, setWCost] = useState<number>(0.25);
  const [wCo2, setWCo2] = useState<number>(0.20);
  const [wPlastic, setWPlastic] = useState<number>(0.15);

  const [loading, setLoading] = useState<boolean>(false);
  const [weightError, setWeightError] = useState<string | null>(null);
  const result = optimizationResult;
  const abortRef = useRef<AbortController | null>(null);

  // Operation Progress State
  const [optStatus, setOptStatus] = useState<OperationStatus>(
    optimizationResult ? 'success' : 'idle'
  );
  const [optStartTime, setOptStartTime] = useState<number | null>(null);
  const [optError, setOptError] = useState<string | null>(null);
  const [searchPhase, setSearchPhase] = useState(
    'The search runs 80 trials in one request. The chart appears when those trials finish, usually in about 20 seconds.'
  );

  useEffect(() => {
    if (!loading || optStartTime == null) return;
    const describe = () => {
      const seconds = Math.max(0, Math.floor((Date.now() - optStartTime) / 1000));
      if (seconds < 20) {
        setSearchPhase(
          `Searching 80 mix trials. Elapsed ${seconds}s of a typical 20 seconds. The server does not report a percentage, so the strength–cost chart stays hidden until the trials finish.`
        );
      } else {
        setSearchPhase(
          `Still searching after ${seconds}s. Typical searches finish in about 20 seconds. The chart will replace this message when the server returns the frontier.`
        );
      }
    };
    describe();
    const timer = window.setInterval(describe, 1000);
    return () => window.clearInterval(timer);
  }, [loading, optStartTime]);

  const normalizeWeights = () => {
    const raw = [wCS, wCost, wCo2, wPlastic];
    const sum = raw.reduce((total, value) => total + value, 0);
    if (sum <= 0) return null;
    return raw.map((val) => Math.round((val / sum) * 1000) / 1000);
  };

  const handleStopWaiting = () => {
    abortRef.current?.abort();
  };

  const handleRunOptimizer = async () => {
    if (loading) return;
    const weights = normalizeWeights();
    if (!weights) {
      setWeightError('Enter at least one objective weight above zero. The search does not invent equal weights.');
      return;
    }
    setWeightError(null);
    cancelOperation();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setOptError(null);
    setOptStatus('running');
    const start = Date.now();
    setOptStartTime(start);

    const [weightCompressive, weightCost, weightCo2, weightPlastic] = weights;
    try {
      const data = await runOptimization({
        mode: 'constrained',
        plastic_type: plasticType === 'Any' ? null : plasticType,
        replacement_pct_max: repMax,
        compressive_strength_min: csMin,
        weight_compressive: weightCompressive,
        weight_cost: weightCost,
        weight_co2: weightCo2,
        weight_plastic_content: weightPlastic,
      }, controller.signal);
      if (controller.signal.aborted) return;
      setOptimizationResult(data);
      setOptStatus('success');
    } catch (e) {
      if (controller.signal.aborted) {
        setOptStatus(optimizationResult ? 'success' : 'cancelled');
        setOptError(optimizationResult ? null : 'Stopped waiting. Run the search again to plot a frontier.');
        return;
      }
      const msg = e instanceof Error ? e.message : 'The mix search did not return candidates.';
      setOptError(msg);
      setOptStatus(msg.toLowerCase().includes('timed out') ? 'timeout' : 'error');
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setLoading(false);
    }
  };

  const handleSelectCandidate = (candidate: TradeoffPoint) => {
    selectCandidate(candidate);
  };

  const handleRevertBaseline = () => {
    selectCandidate(null);
  };

  // Pareto Scatter Data: Strength (Y) vs Cost (X), with size/color info
  const paretoData = result?.tradeoff_points?.map((p, idx) => ({
    id: `Candidate #${idx + 1}`,
    cost: p.predicted_cost_inr_m3,
    cs: p.predicted_cs_mpa,
    replacement: p.recipe?.replacement_pct,
    co2: p.predicted_co2_kgco2e_m3,
    plastic: p.recipe?.plastic_type,
    raw: p,
    isRecommended: idx === 0,
    isSelected: selectedCandidate?.predicted_cost_inr_m3 === p.predicted_cost_inr_m3,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div>
            <h2 className="text-xl font-heading font-bold text-[#1E2022] tracking-tight">
              Find better mix designs
            </h2>
            <p className="text-xs text-[#525866] mt-1 max-w-2xl leading-relaxed">
              Search for candidate mixes that raise predicted strength, lower estimated cost, lower estimated carbon, or use more plastic waste. Objectives can conflict, so there is no single best mix.
            </p>
          </div>
        </div>

        {selectedCandidate ? (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-[#2563EB] bg-[#2563EB]/10 px-2.5 py-1 rounded border border-[#2563EB]/20">
              This candidate is now the mix in use
            </span>
            <button
              onClick={handleRevertBaseline}
              className="px-2.5 py-1 rounded border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-xs font-semibold text-[#525866] transition-colors cursor-pointer"
            >
              Use original mix
            </button>
          </div>
        ) : (
          <span className="text-xs font-mono text-[#525866]">
            Using the mix you entered
          </span>
        )}
      </div>

      {/* 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Constraints & Objective Weights (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
              <span className="eyebrow-tag text-[10px] text-[#525866]">1. Limits for this search</span>
            </div>

            {/* Target Compressive Strength Min */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-[#1E2022]">Minimum predicted compressive strength</span>
                <span className="font-mono text-[#2563EB] font-bold">{csMin} MPa</span>
              </div>
              <FieldHelp>Candidates below this predicted strength are discarded. This is a search filter, not a laboratory pass.</FieldHelp>
              <input
                type="range"
                min="10"
                max="45"
                step="1"
                value={csMin}
                aria-label="Minimum predicted compressive strength in megapascals"
                onChange={(e) => setCsMin(parseFloat(e.target.value))}
                className="w-full h-2 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#525866]">
                <span>10 MPa (M10)</span>
                <span>20 MPa (M20)</span>
                <span>45 MPa (M45)</span>
              </div>
            </div>

            {/* Max Plastic Replacement Pct */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-[#1E2022]">Maximum plastic replacement</span>
                <span className="font-mono text-[#2563EB] font-bold">{repMax} %</span>
              </div>
              <FieldHelp>Upper limit on plastic replacing natural aggregate in the search.</FieldHelp>
              <input
                type="range"
                min="5"
                max="40"
                step="1"
                value={repMax}
                aria-label="Maximum plastic aggregate replacement percent"
                onChange={(e) => setRepMax(parseFloat(e.target.value))}
                className="w-full h-2 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
              />
            </div>

            {/* Polymer Type Filter */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#1E2022] block">
                Polymer type
              </label>
              <FieldHelp>Leave as any polymer, or restrict the search to one plastic type.</FieldHelp>
              <select
                value={plasticType}
                onChange={(e) => setPlasticType(e.target.value)}
                className="w-full text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] text-[#1E2022] px-3 py-2 focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
              >
                <option value="Any">Any polymer</option>
                <option value="PET">Polyethylene Terephthalate (PET)</option>
                <option value="HDPE">High-Density Polyethylene (HDPE)</option>
                <option value="LDPE">Low-Density Polyethylene (LDPE)</option>
                <option value="PVC">Polyvinyl Chloride (PVC)</option>
                <option value="PP">Polypropylene (PP)</option>
                <option value="Mixed">Mixed Post-Consumer Polymers</option>
              </select>
            </div>
          </div>

          {/* Objective Multi-Weights Card */}
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
              <span className="eyebrow-tag text-[10px] text-[#525866]">2. What matters most</span>
            </div>

            <p className="text-[11px] text-[#525866] leading-relaxed">
              These weights are relative and are scaled to add up to 1 before the search. Raising predicted strength can reduce how much the search favours lower cost or lower carbon.
            </p>
            {weightError && (
              <p role="alert" className="text-xs text-[#9A3412] bg-[#FFF7ED] border border-[#F97316]/40 rounded-md px-2.5 py-2">
                {weightError}
              </p>
            )}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-bold text-[#525866] block">Increase predicted strength</span>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={wCS}
                  aria-label="Compressive strength weight"
                  aria-invalid={weightError ? true : undefined}
                  onChange={(e) => setWCS(parseFloat(e.target.value) || 0)}
                  className="mt-1 w-full text-xs font-mono font-bold bg-white border border-[#E5E5E0] rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
                />
              </div>

              <div className="p-2.5 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-bold text-[#525866] block">Reduce estimated material cost</span>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={wCost}
                  onChange={(e) => setWCost(parseFloat(e.target.value) || 0)}
                  className="mt-1 w-full text-xs font-mono font-bold bg-white border border-[#E5E5E0] rounded px-2 py-1"
                />
              </div>

              <div className="p-2.5 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-bold text-[#525866] block">Reduce estimated carbon</span>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={wCo2}
                  onChange={(e) => setWCo2(parseFloat(e.target.value) || 0)}
                  className="mt-1 w-full text-xs font-mono font-bold bg-white border border-[#E5E5E0] rounded px-2 py-1"
                />
              </div>

              <div className="p-2.5 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-bold text-[#525866] block">Increase plastic-waste use</span>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={wPlastic}
                  onChange={(e) => setWPlastic(parseFloat(e.target.value) || 0)}
                  className="mt-1 w-full text-xs font-mono font-bold bg-white border border-[#E5E5E0] rounded px-2 py-1"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleRunOptimizer}
              disabled={loading}
              aria-busy={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-all shadow-xs cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#2563EB]"
            >
              <Sparkles className="w-4 h-4 text-white" />
              <span>{loading ? 'Searching mixes, typically about 20 seconds' : 'Search candidate mixes'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Pareto Frontier & Candidate Selection (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Pareto Frontier Scatter Chart */}
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <div>
                <h3 className="font-heading font-bold text-[#1E2022] text-sm">
                  Best trade-off mixes (predicted strength vs cost)
                </h3>
                <p className="text-xs text-[#525866]">
                  Each point is a returned candidate. Higher and left is stronger at lower estimated cost. Points appear only after the search finishes.
                </p>
              </div>
              <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                {loading ? 'Search running' : result?.tradeoff_points ? `${result.tradeoff_points.length} candidates` : 'Ready'}
              </span>
            </div>

            <div className="min-h-64 w-full">
              {loading || optStatus === 'error' || optStatus === 'timeout' || optStatus === 'cancelled' ? (
                <OperationProgress
                  title={
                    optStatus === 'timeout'
                      ? 'Mix search timed out'
                      : optStatus === 'error'
                      ? 'Mix search failed'
                      : optStatus === 'cancelled'
                      ? 'Stopped waiting for the search'
                      : 'Searching mix candidates'
                  }
                  description={
                    optStatus === 'running'
                      ? searchPhase
                      : optStatus === 'cancelled'
                      ? 'The chart was not updated. Run the search again when you want a frontier.'
                      : 'The strength–cost chart appears only after the trials finish. Your constraints are unchanged.'
                  }
                  status={optStatus === 'idle' ? 'running' : optStatus}
                  startTime={optStartTime}
                  expectedDurationMs={20000}
                  errorMessage={optError}
                  technicalDetails={optError}
                  onRetry={handleRunOptimizer}
                  onCancel={loading ? handleStopWaiting : undefined}
                  cancelLabel="Stop waiting"
                />
              ) : paretoData.length > 0 ? (
                <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" />
                    <XAxis
                      type="number"
                      dataKey="cost"
                      name="Cost"
                      unit=" ₹"
                      stroke="#525866"
                      fontSize={11}
                    />
                    <YAxis
                      type="number"
                      dataKey="cs"
                      name="Strength"
                      unit=" MPa"
                      stroke="#525866"
                      fontSize={11}
                    />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3' }}
                      content={<CandidateTooltip />}
                    />
                    <Scatter
                      name="Candidates"
                      data={paretoData}
                      fill="#2563EB"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-center text-xs text-[#525866] space-y-1 px-6">
                  <span className="font-semibold text-[#1E2022]">No frontier yet</span>
                  <span>Run the search to plot predicted strength against cost. The chart stays empty while 80 trials run, usually about 20 seconds, and then appears with the returned candidates.</span>
                </div>
              )}
            </div>
          </div>

          {/* Top Pareto Candidate Solutions Cards */}
          {!loading && result?.tradeoff_points && result.tradeoff_points.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-heading font-bold text-xs text-[#1E2022] uppercase tracking-wider">
                  Compare candidate mixes
                </h4>
                <span className="text-[10px] text-[#525866]">
                  Selecting a candidate does not erase the mix you entered
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.tradeoff_points.slice(0, 4).map((point, idx) => {
                  const isSelected = selectedCandidate?.predicted_cost_inr_m3 === point.predicted_cost_inr_m3;
                  const isTop = idx === 0;

                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border transition-all ${
                        isSelected
                          ? 'border-[#2563EB] bg-[#2563EB]/5 ring-1 ring-[#2563EB]'
                          : isTop
                          ? 'border-[#2563EB]/40 bg-[#FFFFFF]'
                          : 'border-[#E5E5E0] bg-[#FFFFFF] hover:border-[#333A42]/30'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-heading font-bold text-xs text-[#1E2022]">
                              Candidate #{idx + 1}
                            </span>
                            {isTop && (
                              <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-1.5 py-0.5 rounded border border-[#2563EB]/20">
                                Closest to your weights
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] font-mono text-[#525866] block">
                            {point.recipe.plastic_type} @ {point.recipe.replacement_pct}% repl · w/c {point.recipe.wc_ratio}
                          </span>
                        </div>

                        {isSelected && (
                          <span className="p-1 rounded-full bg-[#2563EB] text-white">
                            <Check className="w-3 h-3" />
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono my-2.5">
                        <div className="p-1.5 rounded bg-[#F5F5F3] border border-[#E5E5E0]">
                          <span className="text-[#525866] text-[10px] block">Predicted strength</span>
                          <span className="font-bold text-[#2563EB]">{point.predicted_cs_mpa != null ? `${point.predicted_cs_mpa.toFixed(1)} MPa` : '—'}</span>
                        </div>
                        <div className="p-1.5 rounded bg-[#F5F5F3] border border-[#E5E5E0]">
                          <span className="text-[#525866] text-[10px] block">Estimated cost</span>
                          <span className="font-bold text-[#1E2022]">{point.predicted_cost_inr_m3 != null ? `₹${point.predicted_cost_inr_m3.toFixed(0)}/m³` : '—'}</span>
                        </div>
                        <div className="p-1.5 rounded bg-[#F5F5F3] border border-[#E5E5E0]">
                          <span className="text-[#525866] text-[10px] block">Estimated carbon</span>
                          <span className="font-bold text-[#1E2022]">{point.predicted_co2_kgco2e_m3 != null ? `${point.predicted_co2_kgco2e_m3.toFixed(0)} kg CO₂e/m³` : '—'}</span>
                        </div>
                        <div className="p-1.5 rounded bg-[#F5F5F3] border border-[#E5E5E0]">
                          <span className="text-[#525866] text-[10px] block">Plastic use</span>
                          <span className="font-bold text-[#1E2022]">{point.predicted_plastic_diversion_kg_m3 != null ? `${point.predicted_plastic_diversion_kg_m3.toFixed(1)} kg/m³` : '—'}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleSelectCandidate(point)}
                        className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                          isSelected
                            ? 'bg-[#333A42] text-white'
                            : 'bg-[#2563EB] hover:bg-[#1D4ED8] text-white shadow-xs'
                        }`}
                      >
                        <span>{isSelected ? 'In use' : 'Use this mix'}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      <TechnicalDetails>
        <p>The search is a constrained Optuna TPE study of 80 trials on the existing property-prediction pipeline. Returned points are the non-dominated trade-offs (Pareto set) for the weights you set.</p>
        <p>Cost is estimated INR/m³ and carbon is estimated kg CO₂e/m³ from the shared mass-balance factors. None of these values is a laboratory measurement.</p>
      </TechnicalDetails>
    </div>
  );
};
