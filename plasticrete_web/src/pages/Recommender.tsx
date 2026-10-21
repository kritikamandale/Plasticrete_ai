import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { APPLICATION_PRETTY_NAMES } from '../types';
import {
  BookOpen,
  DollarSign,
  ExternalLink,
} from 'lucide-react';

export const Recommender: React.FC = () => {
  const { recommendation } = useMix();

  const cb = recommendation?.cost_benefit;
  const analogues = recommendation?.rag_analogues || [];

  return (
    <div className="space-y-6">
      <MixControlPanel />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">
            M4 Construction Application Recommender & RAG Retrieval
          </h2>
          <p className="text-xs font-semibold text-slate-700">
            Random Forest multi-label classification paired with FAISS vector similarity search across published literature
          </p>
        </div>
      </div>

      {/* Top 2 Cards: Best Application & Cost-Benefit Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Primary Classification (5 cols) */}
        <div className="lg:col-span-5 glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">Top Recommended Product</span>
              <span className="text-xs font-mono font-bold text-indigo-900 bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200">
                {recommendation?.primary_confidence_pct}% Match
              </span>
            </div>

            <div className="my-2">
              <h3 className="text-xl font-extrabold text-slate-950">
                {APPLICATION_PRETTY_NAMES[recommendation?.primary_application || ''] || recommendation?.primary_application}
              </h3>
              <p className="text-xs font-semibold text-slate-700 mt-1">
                Optimally satisfies mechanical load limits, density thresholds, and durability conditions.
              </p>
            </div>
          </div>

          {/* Suitable Application Ranking */}
          <div className="pt-4 border-t border-slate-200 space-y-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Suitability Ranking (Top Categories)
            </span>
            {recommendation?.suitability_scores && (
              <div className="space-y-2">
                {Object.entries(recommendation.suitability_scores).slice(0, 4).map(([app, score]) => (
                  <div key={app} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="text-slate-900 font-semibold truncate max-w-[200px]">
                        {APPLICATION_PRETTY_NAMES[app] || app}
                      </span>
                      <span className="font-mono font-bold text-slate-950">
                        {score.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full"
                        style={{ width: `${Math.min(100, score)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Cost-Benefit Economics (7 cols) */}
        <div className="lg:col-span-7 glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-300/80 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-700" />
              <h3 className="font-bold text-slate-950 text-base">
                Cost-Benefit & Commercial Economics (INR / ₹)
              </h3>
            </div>
            <span className="text-xs font-mono font-bold text-emerald-900 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-300">
              {cb?.cost_saving_pct}% Cost Reduction
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-auto py-2">
            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Plastic Mix Cost</span>
              <span className="text-lg font-extrabold font-mono text-emerald-800">
                ₹{cb?.plastic_mix_cost_inr_m3}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">per m³</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Conventional M20</span>
              <span className="text-lg font-bold font-mono text-slate-700">
                ₹{cb?.conventional_cost_inr_m3}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">per m³</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Savings per m³</span>
              <span className="text-lg font-extrabold font-mono text-blue-800">
                ₹{cb?.cost_saving_inr_m3}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">INR saved</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-100 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-0.5">Square Meter Cost</span>
              <span className="text-lg font-extrabold font-mono text-indigo-800">
                ₹{cb?.plastic_mix_cost_inr_m2}
              </span>
              <span className="text-[11px] font-semibold text-slate-600 block">per m² (yield {cb?.product_yield_m2_per_m3}m²)</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 text-xs font-semibold text-slate-800 flex justify-between">
            <span>Material consumption: {cb?.plastic_kg_per_m3} kg plastic + {cb?.additive_kg_per_m3} kg additive per m³</span>
            <span className="text-emerald-800 font-bold font-mono">₹{cb?.cost_saving_inr_m2} saving/m²</span>
          </div>
        </div>
      </div>

      {/* RAG Knowledge Base Section */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-700" />
            <h3 className="font-bold text-slate-950 text-base">
              Literature Analogues (Top-3 FAISS RAG Retrieval Matches)
            </h3>
          </div>
          <span className="text-xs font-semibold text-slate-700">
            Retrieved via normalized 15D vector similarity
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {analogues.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-white border border-slate-300 flex flex-col justify-between hover:shadow-md transition-shadow"
            >
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-extrabold text-slate-950">
                    {item.author} ({item.year})
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-100 text-indigo-900 font-bold border border-indigo-200">
                    Rank #{item.rank}
                  </span>
                </div>

                <p className="text-xs font-medium text-slate-700 italic mb-2">
                  {item.journal}
                </p>

                <div className="space-y-1.5 my-3 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-700 font-semibold">Application:</span>
                    <span className="text-slate-950 font-bold">{item.primary_application}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-700 font-semibold">Tested CS:</span>
                    <span className="text-emerald-800 font-bold">{item.properties.compressive_strength_mpa} MPa</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-700 font-semibold">L2 Distance:</span>
                    <span className="text-slate-900 font-bold">{item.l2_distance.toFixed(3)}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs text-blue-700">
                <span className="font-mono text-[11px] text-slate-700 font-medium truncate max-w-[140px]">{item.doi}</span>
                <span className="inline-flex items-center gap-1 font-bold">
                  DOI <ExternalLink className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
