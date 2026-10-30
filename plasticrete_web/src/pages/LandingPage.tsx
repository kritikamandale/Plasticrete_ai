import React from 'react';
import { useMix } from '../context/MixContext';
import {
  Sparkles,
  ArrowRight,
  FileCheck,
  FlaskConical,
  RotateCcw,
  AlertTriangle,
} from 'lucide-react';
import heroAsset from '../assets/hero.png';

const PLASTIC_TYPES = ['PET', 'HDPE', 'LDPE', 'PVC', 'PP', 'Mixed'];

export const LandingPage: React.FC = () => {
  const { setMainRoute, setStudioTab, mix, setMix, prediction, score, inferenceSource, refreshAll, startNewMix } = useMix();

  const compressive = prediction?.predictions.compressive_strength_mpa;
  const cs = compressive?.mean;
  const csLow = compressive?.ci_90_low;
  const csHigh = compressive?.ci_90_high;
  const co2Savings = score?.co2_saving_pct;
  const diversionKg = score?.plastic_diversion_kg_m3;

  return (
    <div className="space-y-16 py-4">
      {/* ── 1. Hero Section ──────────────────────────────────────────────── */}
      <section className="relative rounded-2xl border border-[#E5E5E0] bg-[#FFFFFF] p-8 sm:p-12 concrete-grid shadow-xs overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Hero Column */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-[#F5F5F3] border border-[#E5E5E0] text-[11px] font-mono text-[#333A42]">
              <span className="h-2 w-2 rounded-full bg-[#2563EB]" />
              <span className="font-bold tracking-wider uppercase text-[10px]">
                ACCELERATING NET-ZERO INFRASTRUCTURE
              </span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-heading font-bold text-[#1E2022] tracking-tight leading-[1.12]">
              Turn Plastic Waste Into Engineered Construction Materials.
            </h1>

            <p className="text-sm sm:text-base text-[#525866] max-w-xl leading-relaxed">
              Design a plastic-waste composite mix a plant can defend. Screen seven material properties, search and score the mix, then write a mix design report and record the laboratory cube on a batch passport.
            </p>

            {/* Supporting Metadata */}
            <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[10px] text-[#525866]">
              <span className="px-2 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] font-semibold">
                SHARED MASS BALANCE
              </span>
              <span className="text-[#E5E5E0]">·</span>
              <span className="px-2 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] font-semibold">
                USE-CLASS GATES
              </span>
              <span className="text-[#E5E5E0]">·</span>
              <span className="px-2 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] font-semibold">
                TRACEABLE BATCH PASSPORTS
              </span>
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
                className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-heading font-bold text-xs uppercase tracking-wider transition-all shadow-xs cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-white" />
                <span>Open mix workspace</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={startNewMix}
                className="inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-lg bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#1E2022] font-heading font-bold text-xs uppercase tracking-wider border border-[#E5E5E0] transition-all cursor-pointer"
              >
                <RotateCcw className="w-4 h-4 text-[#333A42]" />
                <span>Start a new mix</span>
              </button>

              <button
                onClick={() => setMainRoute('standards')}
                className="inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-lg bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#1E2022] font-semibold text-xs border border-[#E5E5E0] transition-all cursor-pointer"
              >
                <FileCheck className="w-4 h-4 text-[#333A42]" />
                <span>Review requirements</span>
              </button>
            </div>
          </div>

          {/* Right Hero Column: Material-focused Graphic with Technical Annotations */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] p-3 shadow-xs">
              <img
                src={heroAsset}
                alt="Recycled plastic flakes, concrete aggregate, and specimen testing"
                className="rounded-lg object-cover w-full h-[320px] filter contrast-[1.05]"
              />

              {/* Technical Annotation Badges */}
              <div className="absolute top-6 left-6 rounded-md bg-[#333A42]/90 backdrop-blur-md text-white px-2.5 py-1.5 border border-white/20 shadow-sm">
                <span className="eyebrow-tag text-[9px] text-[#2563EB] block font-bold">
                  POLYMER INPUT
                </span>
                <span className="font-mono text-xs font-bold">
                  {mix.plastic_type} Shredded Flakes (0.5–12mm)
                </span>
              </div>

              <div className="absolute bottom-6 left-6 right-6 rounded-md bg-[#FFFFFF]/95 backdrop-blur-md p-3 border border-[#E5E5E0] shadow-md flex items-center justify-between">
                <div>
                  <span className="eyebrow-tag text-[9px] text-[#525866] block font-bold">
                    MIX DESIGN & VERIFICATION
                  </span>
                  <span className="font-heading text-xs font-bold text-[#1E2022]">
                    IS 516 Compressive Cube Testing
                  </span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-xs font-bold text-[#2563EB]">
                    {mix.replacement_pct}% Vol. Repl.
                  </span>
                  <span className="block text-[10px] font-mono text-[#525866]">
                    w/c {mix.wc_ratio}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. Interactive Formulation Simulator ─────────────────────────── */}
      <section className="rounded-2xl border border-[#E5E5E0] bg-[#FFFFFF] overflow-hidden shadow-xs">
        {/* Structural Dark Header */}
        <div className="bg-[#333A42] text-white px-6 py-5 border-b border-[#282E34] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[#2563EB]/20 text-[#2563EB] border border-[#2563EB]/40">
              <FlaskConical className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-heading font-bold text-white tracking-tight">
                  Try a mix
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#FFFFFF]/10 text-[#E5E5E0]">
                  SCREENING ESTIMATE
                </span>
              </div>
              <p className="text-xs text-[#E5E5E0]">
                Adjust the material composition to explore the model's predictions.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={startNewMix}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#FFFFFF]/10 hover:bg-[#FFFFFF]/20 text-white text-xs font-semibold transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Start a new mix</span>
            </button>
            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-colors"
            >
              <span>Open mix workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Simulator Grid */}
        <div className="p-6 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Interactive Controls (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Polymer Type */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#1E2022] flex justify-between">
                  <span className="text-[#525866]">Selected Polymer</span>
                  <span className="font-mono text-[#2563EB] font-bold">{mix.plastic_type}</span>
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {PLASTIC_TYPES.map((pt) => (
                    <button
                      key={pt}
                      onClick={() => setMix((prev) => ({ ...prev, plastic_type: pt }))}
                      className={`px-2.5 py-2 rounded-md text-xs font-semibold font-mono border transition-all cursor-pointer ${
                        mix.plastic_type === pt
                          ? 'bg-[#333A42] text-white border-[#333A42] shadow-xs'
                          : 'bg-[#FFFFFF] text-[#525866] border-[#E5E5E0] hover:bg-[#F5F5F3]'
                      }`}
                    >
                      {pt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Water-Cement Ratio */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[#525866]">Water / Cement Ratio</span>
                  <span className="font-mono text-[#1E2022] font-bold">{mix.wc_ratio}</span>
                </div>
                <input
                  type="range"
                  min="0.30"
                  max="0.65"
                  step="0.01"
                  value={mix.wc_ratio}
                  onChange={(e) => setMix((prev) => ({ ...prev, wc_ratio: parseFloat(e.target.value) }))}
                  className="w-full h-2 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
                />
                <div className="flex justify-between text-[10px] font-mono text-[#525866]">
                  <span>0.30</span>
                  <span>IS Default: 0.45</span>
                  <span>0.65</span>
                </div>
              </div>
            </div>

            {/* Plastic Replacement Slider */}
            <div className="p-4 rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] space-y-3">
              <div className="flex justify-between items-center text-xs font-semibold">
                <div>
                  <span className="text-[#1E2022] font-bold block">Plastic Aggregate Replacement</span>
                  <span className="text-[11px] text-[#525866]">Volumetric substitution of natural coarse aggregate</span>
                </div>
                <span className="text-xl font-bold font-mono text-[#2563EB] bg-[#FFFFFF] px-3 py-1 rounded-md border border-[#E5E5E0]">
                  {mix.replacement_pct}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="40"
                step="1"
                value={mix.replacement_pct}
                onChange={(e) => setMix((prev) => ({ ...prev, replacement_pct: parseFloat(e.target.value) }))}
                className="w-full h-2.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#525866]">
                <span>0% Control</span>
                <span>10% Low</span>
                <span>20% Structural Limit</span>
                <span>40% Max Screening</span>
              </div>
            </div>

            {/* Particle Size & Mineral Additives */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[#525866]">Gradation (Particle Size)</span>
                  <span className="font-mono text-[#1E2022] font-bold">{mix.particle_size_mm} mm</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="12.0"
                  step="0.5"
                  value={mix.particle_size_mm}
                  onChange={(e) => setMix((prev) => ({ ...prev, particle_size_mm: parseFloat(e.target.value) }))}
                  className="w-full h-2 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[#525866]">Pozzolan Dosage (Fly Ash / Silica)</span>
                  <span className="font-mono text-[#1E2022] font-bold">{mix.additive_pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="30"
                  step="1"
                  value={mix.additive_pct}
                  onChange={(e) => setMix((prev) => ({ ...prev, additive_pct: parseFloat(e.target.value) }))}
                  className="w-full h-2 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
                />
              </div>
            </div>
          </div>

          {/* Right: Results Panel (5 cols) */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
            {/* Status & Alerts */}
            {inferenceSource === 'unavailable' && (
              <div className="p-3 rounded-lg border border-[#F97316]/40 bg-[#FFF7ED] text-xs text-[#1E2022] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0" />
                  <span>The prediction service is temporarily unavailable. Your saved mix is unchanged.</span>
                </div>
                <button
                  onClick={() => refreshAll()}
                  className="px-2 py-1 rounded bg-white text-[11px] font-bold text-[#1E2022] border border-[#E5E5E0]"
                >
                  Retry
                </button>
              </div>
            )}

            {mix.replacement_pct > 25 && (
              <div className="p-3 rounded-lg border border-[#F97316]/40 bg-[#FFF7ED] text-xs text-[#1E2022] flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0" />
                <span>
                  <strong>Experimental screening mix:</strong> High plastic volume (&gt;25%) degrades bond matrix. Laboratory testing required before use.
                </span>
              </div>
            )}

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Compressive Strength */}
              <div className="p-4 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
                <span className="eyebrow-tag text-[9px] text-[#525866] block">
                  PREDICTED STRENGTH
                </span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-3xl font-bold font-mono text-[#1E2022]">
                    {cs != null ? cs.toFixed(1) : '—'}
                  </span>
                  <span className="text-xs font-semibold text-[#525866] font-mono">MPa</span>
                </div>
                {csLow != null && csHigh != null ? (
                  <span className="inline-block mt-2 font-mono text-[10px] text-[#2563EB] bg-[#2563EB]/10 px-1.5 py-0.5 rounded font-bold">
                    90% CI: [{csLow.toFixed(1)}–{csHigh.toFixed(1)}]
                  </span>
                ) : (
                  <span className="inline-block mt-2 font-mono text-[10px] text-[#525866]">
                    Interval unavailable
                  </span>
                )}
              </div>

              {/* Carbon Reduction */}
              <div className="p-4 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
                <span className="eyebrow-tag text-[9px] text-[#525866] block">
                  EMBODIED CO₂ SAVED
                </span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-3xl font-bold font-mono text-[#2563EB]">
                    {co2Savings != null ? `${co2Savings}%` : '—'}
                  </span>
                </div>
                <span className="inline-block mt-2 font-mono text-[10px] text-[#525866]">
                  vs. M20 baseline (ICE v4.1)
                </span>
              </div>

              {/* Plastic Diverted */}
              <div className="p-4 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
                <span className="eyebrow-tag text-[9px] text-[#525866] block">
                  PLASTIC DIVERTED
                </span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold font-mono text-[#1E2022]">
                    {diversionKg != null ? diversionKg.toFixed(0) : '—'}
                  </span>
                  <span className="text-xs font-semibold text-[#525866] font-mono">kg/m³</span>
                </div>
                <span className="inline-block mt-2 font-mono text-[10px] text-[#525866]">
                  Landfill diversion mass
                </span>
              </div>

              {/* Targets Evaluated */}
              <div className="p-4 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
                <span className="eyebrow-tag text-[9px] text-[#525866] block">
                  PREDICTION SCOPE
                </span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold font-mono text-[#1E2022]">7</span>
                  <span className="text-xs font-semibold text-[#525866] font-mono">Properties</span>
                </div>
                <span className="inline-block mt-2 font-mono text-[10px] text-[#2563EB] font-bold">
                  Property prediction
                </span>
              </div>
            </div>

            {/* Bottom Disclaimer */}
            <div className="p-3 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0] text-[11px] text-[#525866] leading-relaxed">
              <strong className="text-[#1E2022]">Verification Notice:</strong> Predictions are statistical screening estimates. Compliance requires IS 516 destructive cube testing on a verified trial batch.
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. Five Core Modules ─────────────────────────────────────────── */}
      <section className="space-y-6">
        <div>
          <span className="eyebrow-tag text-[10px] text-[#2563EB] block">
            INTEGRATED WORKSPACE
          </span>
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-[#1E2022] tracking-tight">
            Five steps. One mix record.
          </h2>
          <p className="text-xs sm:text-sm text-[#525866] max-w-2xl mt-1 leading-relaxed">
            Define a mix, predict performance, compare candidates, review environmental impact, then write a mix report and record the laboratory cube.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Module 01 */}
          <div className="engineering-card rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
                <span className="font-mono text-xs font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                  MODULE 01
                </span>
                <span className="text-xs text-[#525866] font-mono">Seven properties</span>
              </div>

              <h3 className="text-lg font-heading font-bold text-[#1E2022] mb-2">
                Predict concrete performance
              </h3>

              <p className="text-xs text-[#525866] leading-relaxed mb-4">
                Estimate compressive, flexural and tensile strength, density, water absorption, thermal conductivity and durability for the mix you entered.
              </p>

              {/* Property Tags */}
              <div className="flex flex-wrap gap-1.5 mb-6">
                {[
                  'Compressive Strength',
                  'Flexural Strength',
                  'Split Tensile Strength',
                  'Bulk Density',
                  'Water Absorption',
                  'Thermal Conductivity',
                  'Durability Index',
                  'Why this prediction',
                ].map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded bg-[#F5F5F3] text-[11px] font-medium text-[#333A42] border border-[#E5E5E0]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('predictor'); }}
              className="inline-flex items-center justify-between pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8] transition-colors cursor-pointer"
            >
              <span>Predict this mix</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Module 02 */}
          <div className="engineering-card rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
                <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                  MODULE 02
                </span>
                <span className="text-xs text-[#525866] font-mono">Candidate mixes</span>
              </div>

              <h3 className="text-lg font-heading font-bold text-[#1E2022] mb-2">
                Improve your mix
              </h3>

              <p className="text-xs text-[#525866] leading-relaxed mb-4">
                Search candidate mixes for predicted strength, estimated cost, estimated carbon, and plastic-waste use. Trade-offs are shown because objectives can conflict.
              </p>

              <div className="flex flex-wrap gap-1.5 mb-6">
                {[
                  'Increase predicted strength',
                  'Reduce estimated cost',
                  'Reduce estimated carbon',
                  'Increase plastic-waste use',
                  'Strength limits',
                ].map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded bg-[#F5F5F3] text-[11px] font-medium text-[#333A42] border border-[#E5E5E0]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('optimizer'); }}
              className="inline-flex items-center justify-between pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8] transition-colors cursor-pointer"
            >
              <span>Find better mixes</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Module 03 */}
          <div className="engineering-card rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
                <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                  MODULE 03
                </span>
                <span className="text-xs text-[#525866] font-mono">ICE v4.1 & IS Gates</span>
              </div>

              <h3 className="text-lg font-heading font-bold text-[#1E2022] mb-2">
                Environmental impact and requirements
              </h3>

              <p className="text-xs text-[#525866] leading-relaxed mb-4">
                Estimate carbon and cost from the mix quantities, then screen against selected Indian Standard use-class limits. Screening is not a certificate.
              </p>

              <div className="flex flex-wrap gap-1.5 mb-6">
                {[
                  'Material quantities',
                  'Estimated carbon (kg CO₂e)',
                  'Estimated cost (INR/m³)',
                  'IS 15658 screening',
                  'IS 2185 screening',
                ].map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded bg-[#F5F5F3] text-[11px] font-medium text-[#333A42] border border-[#E5E5E0]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
              className="inline-flex items-center justify-between pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8] transition-colors cursor-pointer"
            >
              <span>Review environmental impact</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Module 04 */}
          <div className="engineering-card rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
                <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                  MODULE 04
                </span>
                <span className="text-xs text-[#525866] font-mono">Uses and references</span>
              </div>

              <h3 className="text-lg font-heading font-bold text-[#1E2022] mb-2">
                Explore applications
              </h3>

              <p className="text-xs text-[#525866] leading-relaxed mb-4">
                See which construction uses this mix is suggested for, and open supporting technical references when they are returned.
              </p>

              <div className="flex flex-wrap gap-1.5 mb-6">
                {[
                  'Suggested uses',
                  'Technical references',
                  'DOI links when returned',
                  'Estimated material cost',
                ].map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded bg-[#F5F5F3] text-[11px] font-medium text-[#333A42] border border-[#E5E5E0]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('recommender'); }}
              className="inline-flex items-center justify-between pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8] transition-colors cursor-pointer"
            >
              <span>Explore applications</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Module 05 */}
          <div className="engineering-card rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] flex flex-col justify-between md:col-span-2">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
                <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                  MODULE 05
                </span>
                <span className="text-xs text-[#525866] font-mono">PDF report + IS 516</span>
              </div>

              <h3 className="text-lg font-heading font-bold text-[#1E2022] mb-2">
                Mix Design Report & Batch Passport
              </h3>

              <p className="text-xs text-[#525866] leading-relaxed mb-4 max-w-3xl">
                Write the shared mass balance, predicted properties, use-class gates, and literature notes into a mix design report. Cast the mix and record the laboratory cube on its passport. A report is a screening record, not a certificate.
              </p>

              <div className="flex flex-wrap gap-1.5 mb-6">
                {[
                  'Mix design PDF',
                  'Mass-balance ledger',
                  '90% prediction interval',
                  'Cast & Record',
                  'IS 516 cube test',
                ].map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 rounded bg-[#F5F5F3] text-[11px] font-medium text-[#333A42] border border-[#E5E5E0]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => setMainRoute('batch')}
              className="inline-flex items-center justify-between pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:text-[#1D4ED8] transition-colors cursor-pointer"
            >
              <span>Open Cast & Record</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ── 4. Engineering Workflow ───────────────────────────────────────── */}
      <section className="rounded-2xl border border-[#E5E5E0] bg-[#FFFFFF] p-8 sm:p-10 shadow-xs">
        <div className="mb-8">
          <span className="eyebrow-tag text-[10px] text-[#2563EB] block">
            STAGE-GATE METHODOLOGY
          </span>
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-[#1E2022] tracking-tight">
            From Plastic Flake to Verified Batch
          </h2>
          <p className="text-xs sm:text-sm text-[#525866] mt-1">
            An empirical, stage-gated civil engineering framework connecting simulation to physical cube validation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          {/* Step 1 */}
          <div className="p-5 rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] relative">
            <span className="font-mono text-xs font-bold text-[#2563EB] block mb-2">
              01 — DEFINE YOUR MIX
            </span>
            <h4 className="font-heading font-bold text-[#1E2022] text-sm mb-2">
              Mix proportions
            </h4>
            <p className="text-xs text-[#525866] leading-relaxed">
              Specify polymer type, aggregate replacement, particle gradation, water/cement ratio, and other supported mixture parameters.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-5 rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] relative">
            <span className="font-mono text-xs font-bold text-[#2563EB] block mb-2">
              02 — PREDICT PERFORMANCE
            </span>
            <h4 className="font-heading font-bold text-[#1E2022] text-sm mb-2">
              Predicted properties
            </h4>
            <p className="text-xs text-[#525866] leading-relaxed">
              Estimate seven concrete properties, with a prediction range when the service returns one.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-5 rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] relative">
            <span className="font-mono text-xs font-bold text-[#2563EB] block mb-2">
              03 — REQUIREMENTS
            </span>
            <h4 className="font-heading font-bold text-[#1E2022] text-sm mb-2">
              Screening, not certification
            </h4>
            <p className="text-xs text-[#525866] leading-relaxed">
              Check the intended application against its applicable requirements. Keep structural applications subject to appropriate engineering review.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-5 rounded-xl border border-[#E5E5E0] bg-[#F5F5F3] relative">
            <span className="font-mono text-xs font-bold text-[#2563EB] block mb-2">
              04 — VERIFICATION
            </span>
            <h4 className="font-heading font-bold text-[#1E2022] text-sm mb-2">
              Batch Verification
            </h4>
            <p className="text-xs text-[#525866] leading-relaxed">
              Record actual test results, material quantities, emissions assumptions, and traceable batch information in the laboratory passport.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
