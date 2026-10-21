import React from 'react';
import { useMix } from '../context/MixContext';
import {
  Cpu,
  Brain,
  Layers,
  Database,
  ArrowRight,
  GitBranch,
  ChevronRight,
  Home,
  CheckCircle2,
} from 'lucide-react';

export const TechPage: React.FC = () => {
  const { setMainRoute, setStudioTab } = useMix();

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-4">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-slate-800 font-bold">
        <button
          onClick={() => setMainRoute('home')}
          className="flex items-center gap-1 hover:text-slate-950 transition-colors cursor-pointer"
        >
          <Home className="w-4 h-4 text-slate-700" />
          <span>Home</span>
        </button>
        <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
        <span className="text-slate-950 font-extrabold">Machine Learning Architecture</span>
      </div>

      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-950 text-xs font-bold border border-blue-300 mb-3">
          <Cpu className="w-4 h-4 text-blue-800" />
          <span>Multi-Stage Scientific ML Pipeline</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-950 tracking-tight">
          System Architecture & Model Deep Dive
        </h1>
        <p className="text-sm font-semibold text-slate-800 mt-2 max-w-3xl leading-relaxed">
          How PlastiCrete AI integrates gradient boosting, deep transfer learning, surrogate-model Bayesian optimization, and vector similarity search into a unified civil-engineering engine.
        </p>
      </div>

      {/* Architecture Flow Diagram */}
      <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm">
        <h3 className="font-extrabold text-slate-950 text-base mb-4">
          Data Flow & Model Integration Pipeline
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200">
            <span className="text-emerald-800 font-extrabold block mb-1">STAGE 1: INPUT</span>
            <p className="text-slate-800 font-sans text-xs font-medium leading-relaxed">
              8 physical inputs: polymer type, replacement %, particle gradation, w/c, pozzolans, curing temp & age.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200">
            <span className="text-blue-800 font-extrabold block mb-1">STAGE 2: M1 ENSEMBLE</span>
            <p className="text-slate-800 font-sans text-xs font-medium leading-relaxed">
              Weighted combination: XGBoost (70%) + Random Forest (20%) + PyTorch DNN (10%) with TreeSHAP.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200">
            <span className="text-indigo-800 font-extrabold block mb-1">STAGE 3: M2 & M3 CORES</span>
            <p className="text-slate-800 font-sans text-xs font-medium leading-relaxed">
              Optuna TPE surrogate searches Pareto front; ICE 3.0 factors compute cradle-to-gate LCA carbon & BIS pass.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200">
            <span className="text-teal-800 font-extrabold block mb-1">STAGE 4: M4 RAG</span>
            <p className="text-slate-800 font-sans text-xs font-medium leading-relaxed">
              RF multi-label classifier targets 12 precast classes; FAISS retrieves top-3 peer-reviewed analogue recipes.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Tech Deep Dives */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* XGBoost + DNN */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-800">
              <Brain className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-slate-950 text-base">
              M1: Multi-Target Ensemble Predictor
            </h3>
          </div>
          <p className="text-xs text-slate-800 font-medium leading-relaxed">
            Trained on 2,000+ experimental mix proportions. Features robust KNN imputation and interaction terms (e.g. <code>plastic_% × w/c</code> and <code>additive_% × curing_days</code>). Produces 5th and 95th percentile confidence intervals to quantify extrapolation uncertainty.
          </p>
          <ul className="text-xs text-slate-900 font-semibold space-y-1.5 font-mono pt-2">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>R² = 0.94 on compressive strength</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>R² = 0.88 on flexural & split tensile</span>
            </li>
          </ul>
        </div>

        {/* Optuna Surrogate */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-100 text-indigo-800">
              <GitBranch className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-slate-950 text-base">
              M2: Surrogate Bayesian Optimization
            </h3>
          </div>
          <p className="text-xs text-slate-800 font-medium leading-relaxed">
            Replaces slow physics iterations with lightweight XGBoost surrogate models that predict cost, CS, CO₂, and diversion. Optuna TPE sampler runs 120 constrained trials in under 200ms to map the non-dominated Pareto frontier.
          </p>
          <ul className="text-xs text-slate-900 font-semibold space-y-1.5 font-mono pt-2">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>&lt;200ms solve time per scenario</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>Strict feasibility barrier functions</span>
            </li>
          </ul>
        </div>

        {/* LCA Physics Engine */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-100 text-emerald-800">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-slate-950 text-base">
              M3: Deterministic LCA & BIS Auditor
            </h3>
          </div>
          <p className="text-xs text-slate-800 font-medium leading-relaxed">
            Uses Inventory of Carbon & Energy (ICE 3.0) emission factors and volumetric displacement formulas. Calculates negative carbon credits for diverted municipal plastic waste (-1.10 kg CO₂e/kg PET) and applies IS 10262 reference concrete benchmarks.
          </p>
          <ul className="text-xs text-slate-900 font-semibold space-y-1.5 font-mono pt-2">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>Full cradle-to-gate LCA accounting</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>Prescriptive remediation advisor</span>
            </li>
          </ul>
        </div>

        {/* FAISS Vector RAG */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-100 text-cyan-800">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-slate-950 text-base">
              M4: FAISS Vector RAG Retrieval
            </h3>
          </div>
          <p className="text-xs text-slate-800 font-medium leading-relaxed">
            Features an indexed vector store of peer-reviewed experimental literature mixes. Using Euclidean L2 distance across 15 normalized mix and property dimensions, it retrieves the nearest published empirical matches with author, journal, and DOI.
          </p>
          <ul className="text-xs text-slate-900 font-semibold space-y-1.5 font-mono pt-2">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>Sub-millisecond FAISS vector search</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>Real commercial cost breakdown (₹/m²)</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="text-center pt-4">
        <button
          onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
          className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-slate-900 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
        >
          <span>Test Models in AI Studio</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
