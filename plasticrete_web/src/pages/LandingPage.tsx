import React from 'react';
import { useMix } from '../context/MixContext';
import {
  Sparkles,
  ArrowRight,
  Leaf,
  Activity,
  Layers,
  FileCheck,
  Scale,
  FlaskConical,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { setMainRoute, setStudioTab, mix, setMix, prediction, score } = useMix();

  const compressive = prediction?.predictions.compressive_strength_mpa;
  const cs = compressive?.mean;
  const co2Savings = score?.co2_saving_pct;

  return (
    <div className="relative overflow-hidden">
      {/* Background Ambient Glows */}
      <div className="ambient-glow-emerald w-96 h-96 top-10 left-1/4 -translate-x-1/2" />
      <div className="ambient-glow-cyan w-96 h-96 top-40 right-10" />
      <div className="ambient-glow-indigo w-96 h-96 top-[800px] left-10" />

      {/* ── 1. Hero Section ──────────────────────────────────────────────── */}
      <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28">
        <div className="max-w-5xl mx-auto text-center px-4">
          {/* Top Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass-pill text-xs font-semibold text-emerald-800 border border-emerald-200/80 mb-6 shadow-sm">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Accelerating Net-Zero Infrastructure</span>
            <span className="text-emerald-300">|</span>
            <span className="text-slate-600 font-medium">Shared mass balance · use-class gates</span>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.12] mb-6">
            Design a plastic-waste mix a plant can defend, then{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent">
              cast one verification cube.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed mb-10">
            Screen seven properties with a 90% interval, one shared carbon number, and a use-class gate. A crush test still decides the batch.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
              className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-2xl bg-slate-900 hover:bg-emerald-600 text-white font-bold text-sm shadow-xl shadow-slate-900/10 hover:shadow-emerald-500/20 transition-all cursor-pointer group"
            >
              <Sparkles className="w-4 h-4 text-emerald-400 group-hover:rotate-12 transition-transform" />
              <span>Launch AI Studio</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => setMainRoute('standards')}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl glass-card text-slate-700 font-semibold text-sm hover:text-slate-900 transition-all cursor-pointer"
            >
              <FileCheck className="w-4 h-4 text-slate-700" />
              <span>Explore BIS Standards</span>
            </button>
          </div>
        </div>

        {/* ── Hero Glass Interactive Widget ─────────────────────────────────── */}
        <div className="max-w-4xl mx-auto mt-14 px-4">
          <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-2xl border border-white/80 relative z-10">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-200 gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-emerald-100 text-emerald-800">
                  <FlaskConical className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-950 text-base">
                    Interactive Formulation Simulator
                  </h3>
                  <p className="text-xs font-semibold text-slate-700">
                    Drag the aggregate replacement slider to see real-time inference
                  </p>
                </div>
              </div>
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
                className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 self-start sm:self-auto cursor-pointer"
              >
                <span>Full Studio Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Slider & Outcome Row */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-6 items-center">
              {/* Slider Control */}
              <div className="md:col-span-6 space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-bold text-slate-800 mb-1.5">
                    <span>Plastic Aggregate Replacement:</span>
                    <span className="font-mono text-emerald-600 font-extrabold text-sm">
                      {mix.replacement_pct}% by volume
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="40"
                    step="1"
                    value={mix.replacement_pct}
                    onChange={(e) => setMix((prev) => ({ ...prev, replacement_pct: parseFloat(e.target.value) }))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs font-mono font-bold text-slate-700 mt-1">
                    <span>0% Plain Concrete</span>
                    <span>20% High-Density</span>
                    <span>40% Max</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
                    <span className="text-xs font-bold text-slate-700 block">Selected Polymer</span>
                    <span className="font-bold text-slate-950">{mix.plastic_type} Aggregate</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">
                    <span className="text-xs font-bold text-slate-700 block">Water/Cement</span>
                    <span className="font-bold text-slate-950">{mix.wc_ratio} w/c</span>
                  </div>
                </div>
              </div>

              {/* Dynamic Readouts */}
              <div className="md:col-span-6 grid grid-cols-2 gap-3">
                <div className="p-4 rounded-2xl bg-white border border-slate-300 shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-bold text-slate-800">Predicted CS</span>
                  <div className="my-1.5">
                    <span className="text-3xl font-extrabold font-mono text-slate-950">{cs == null ? '—' : cs}</span>
                    <span className="text-xs font-bold text-slate-700 font-mono ml-1">MPa</span>
                  </div>
                  <span className="text-xs text-slate-700 font-semibold">
                    {compressive?.ci_90_low == null || compressive?.ci_90_high == null
                      ? '90% interval not returned'
                      : `90% interval ${compressive.ci_90_low}–${compressive.ci_90_high} MPa`}
                  </span>
                  <span className="text-[11px] text-slate-600 font-semibold mt-1">
                    Screening estimate. Not a substitute for IS-compliant laboratory testing or a structural engineer's sign-off.
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-white border border-slate-300 shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-bold text-slate-800">Carbon Reduction</span>
                  <div className="my-1.5">
                    <span className="text-3xl font-extrabold font-mono text-emerald-800">{co2Savings == null ? '—' : `${co2Savings}%`}</span>
                    <span className="text-xs font-bold text-slate-700 font-mono ml-1">CO₂e</span>
                  </div>
                  <span className="text-xs text-slate-700 font-semibold">
                    vs conventional baseline
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. Telemetry Stats Banner ──────────────────────────────────────── */}
      <section className="py-12 border-y border-slate-300/80 bg-white/70 backdrop-blur-sm relative z-10">
        <div className="max-w-6xl mx-auto px-4 grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-slate-950">7 Targets</div>
            <div className="text-xs font-bold text-slate-800 mt-1">Simultaneous property predictions</div>
          </div>
          <div>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-emerald-800">90%</div>
            <div className="text-xs font-bold text-slate-800 mt-1">Interval used by the use-class gate</div>
          </div>
          <div>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-cyan-800">R² 0.91</div>
            <div className="text-xs font-bold text-slate-800 mt-1">Compressive strength, n = 455</div>
          </div>
          <div>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-indigo-800">4 gates</div>
            <div className="text-xs font-bold text-slate-800 mt-1">Paver, hollow, solid, structural</div>
          </div>
        </div>
      </section>

      {/* ── 3. Four Core Pillars Section ────────────────────────────────────── */}
      <section className="py-20 relative z-10">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 block mb-2">
              End-to-End Civil ML Architecture
            </span>
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Four Modules. One Unified Platform.
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Engineered with rigorous civil-engineering physics, Life Cycle Assessment (LCA), and vector RAG retrieval.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Module 1 */}
            <div className="glass-card rounded-3xl p-7 border border-white/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-2xl bg-blue-50 text-blue-600">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600">Module 1</span>
                    <h3 className="font-bold text-slate-900 text-lg">Multi-Target Property Predictor</h3>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  Multi-model ensemble combining XGBoost gradient boosting, Random Forest variance reduction, and PyTorch deep neural networks to forecast 7 physical properties with 90% confidence intervals.
                </p>
                <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Compressive (CS)</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Flexural</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Tensile</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Bulk Density</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Water Abs.</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Durability</span>
                </div>
              </div>
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
                className="mt-6 pt-4 border-t border-slate-100 text-xs font-semibold text-blue-600 flex items-center gap-1.5 hover:gap-2 transition-all cursor-pointer"
              >
                <span>Launch Predictor Engine</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Module 2 */}
            <div className="glass-card rounded-3xl p-7 border border-white/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-2xl bg-indigo-50 text-indigo-600">
                    <Scale className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">Module 2</span>
                    <h3 className="font-bold text-slate-900 text-lg">Mix search on the M1 ensemble</h3>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  Optuna searches recipes by calling the same M1 ensemble the predictor uses, then prices them from the shared mass-balance table. The result is a full recipe and up to three trade-off points.
                </p>
                <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Optuna TPE</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Multi-Objective</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Cost Minimization</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Waste Maximization</span>
                </div>
              </div>
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('optimizer'); }}
                className="mt-6 pt-4 border-t border-slate-100 text-xs font-semibold text-indigo-600 flex items-center gap-1.5 hover:gap-2 transition-all cursor-pointer"
              >
                <span>Search mixes</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Module 3 */}
            <div className="glass-card rounded-3xl p-7 border border-white/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-600">
                    <Leaf className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600">Module 3</span>
                    <h3 className="font-bold text-slate-900 text-lg">Mass balance and use-class gates</h3>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  Carbon and cost come from one dated factor table (ICE v4.1). A product is allowed only when its own standard clears on the lower confidence bound.
                </p>
                <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">ICE v4.1 table</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Use-class gate</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">IS 2185 Blocks</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">LEED / GRIHA / IGBC</span>
                </div>
              </div>
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
                className="mt-6 pt-4 border-t border-slate-100 text-xs font-semibold text-emerald-600 flex items-center gap-1.5 hover:gap-2 transition-all cursor-pointer"
              >
                <span>Open mass balance</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Module 4 */}
            <div className="glass-card rounded-3xl p-7 border border-white/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-2xl bg-cyan-50 text-cyan-600">
                    <Layers className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600">Module 4</span>
                    <h3 className="font-bold text-slate-900 text-lg">Application Finder & Literature RAG</h3>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  Random Forest multi-label classification across 12 industrial construction product categories. Employs a FAISS vector index to retrieve peer-reviewed analogue mixes with DOI citations.
                </p>
                <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">12 Product Classes</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">FAISS 15D Vector</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">Economics (INR/m²)</span>
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">DOI Analogues</span>
                </div>
              </div>
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('recommender'); }}
                className="mt-6 pt-4 border-t border-slate-100 text-xs font-semibold text-cyan-600 flex items-center gap-1.5 hover:gap-2 transition-all cursor-pointer"
              >
                <span>Find Commercial Products</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. Workflow Step-by-Step ────────────────────────────────────────── */}
      <section className="py-20 bg-gradient-to-b from-transparent via-slate-100/50 to-transparent relative z-10">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center max-w-xl mx-auto mb-14">
            <span className="text-xs font-extrabold uppercase tracking-wider text-slate-800 block mb-1">
              Engineering Workflow
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-950">
              From this week's flake to a batch passport
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl glass-card border border-slate-300">
              <span className="text-2xl font-extrabold font-mono text-emerald-800 block mb-2">01</span>
              <h4 className="font-bold text-slate-950 text-sm mb-1">Recipe Input</h4>
              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                Specify plastic polymer (PET/HDPE/LDPE/PVC), particle gradation, w/c ratio, and supplementary cementitious materials.
              </p>
            </div>

            <div className="p-5 rounded-2xl glass-card border border-slate-300">
              <span className="text-2xl font-extrabold font-mono text-blue-800 block mb-2">02</span>
              <h4 className="font-bold text-slate-950 text-sm mb-1">Multi-ML Inference</h4>
              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                The ensemble returns seven properties and a 90% interval. The gate uses the conservative side of that interval.
              </p>
            </div>

            <div className="p-5 rounded-2xl glass-card border border-slate-300">
              <span className="text-2xl font-extrabold font-mono text-indigo-800 block mb-2">03</span>
              <h4 className="font-bold text-slate-950 text-sm mb-1">Standards Check</h4>
              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                A paver, a hollow block, and a solid block each wait for their own standard. Structural use stays a lab trial.
              </p>
            </div>

            <div className="p-5 rounded-2xl glass-card border border-slate-300">
              <span className="text-2xl font-extrabold font-mono text-teal-800 block mb-2">04</span>
              <h4 className="font-bold text-slate-950 text-sm mb-1">Commercialization</h4>
              <p className="text-xs font-medium text-slate-800 leading-relaxed">
                Get optimal precast product categories, cost-benefit savings in INR/m², and peer-reviewed reference analogues.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. Bottom Call to Action Banner ─────────────────────────────────── */}
      <section className="py-20 relative z-10 px-4">
        <div className="max-w-4xl mx-auto glass-card rounded-3xl p-8 sm:p-12 text-center border border-white relative overflow-hidden shadow-2xl">
          <div className="ambient-glow-emerald w-72 h-72 -top-20 -left-20" />
          <div className="ambient-glow-cyan w-72 h-72 -bottom-20 -right-20" />

          <div className="relative z-10 max-w-xl mx-auto space-y-5">
            <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs">
              Live & Fully Integrated
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Ready to Formulate Your Sustainable Mix?
            </h2>
            <p className="text-xs sm:text-sm text-slate-600">
              Open the studio. Strength, carbon, and product gates come from the running model.
            </p>
            <div className="pt-2">
              <button
                onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
                className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-slate-900 hover:bg-emerald-600 text-white font-bold text-sm shadow-xl transition-all cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>Open PlastiCrete AI Studio</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
