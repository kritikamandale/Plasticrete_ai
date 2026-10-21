import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { Brain, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';

export const Explainability: React.FC = () => {
  const { prediction } = useMix();
  const [selectedTarget, setSelectedTarget] = useState<'compressive_strength_mpa' | 'durability_index'>(
    'compressive_strength_mpa'
  );

  const shapDict = prediction?.shap_values[selectedTarget] || {};

  const chartData = Object.entries(shapDict).map(([feature, impact]) => ({
    feature: feature.replace('_', ' '),
    impact: typeof impact === 'number' ? impact : parseFloat(String(impact)),
  })).sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  return (
    <div className="space-y-6">
      <MixControlPanel />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-slate-950">
              SHAP Explainability & Feature Contribution Engine
            </h2>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-900 border border-blue-300">
              <Brain className="w-3.5 h-3.5" />
              TreeSHAP
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-700 mt-1">
            Quantifies the exact local contribution of each mix parameter (in original physical units) to the predicted outcome
          </p>
        </div>

        {/* Target Selector Tabs */}
        <div className="flex rounded-xl bg-slate-200 p-1 border border-slate-300 text-xs font-bold shadow-sm">
          <button
            onClick={() => setSelectedTarget('compressive_strength_mpa')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              selectedTarget === 'compressive_strength_mpa'
                ? 'bg-white font-extrabold text-slate-950 shadow-sm border border-slate-300'
                : 'text-slate-700 hover:text-slate-950 hover:bg-white/60'
            }`}
          >
            Compressive Strength (MPa)
          </button>
          <button
            onClick={() => setSelectedTarget('durability_index')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              selectedTarget === 'durability_index'
                ? 'bg-white font-extrabold text-slate-950 shadow-sm border border-slate-300'
                : 'text-slate-700 hover:text-slate-950 hover:bg-white/60'
            }`}
          >
            Durability Index (/100)
          </button>
        </div>
      </div>

      {/* Main SHAP Chart Card */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
          <div>
            <h3 className="font-bold text-slate-950 text-base">
              Local SHAP Waterfall (Feature Impacts on Current Mix)
            </h3>
            <p className="text-xs font-semibold text-slate-700">
              Green bars represent positive performance drivers; Red bars represent limiting factors
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-bold">
            <span className="flex items-center gap-1.5 text-emerald-800">
              <span className="w-3 h-3 rounded-sm bg-emerald-600" />
              <span>Positive Driver (+Δ)</span>
            </span>
            <span className="flex items-center gap-1.5 text-rose-800">
              <span className="w-3 h-3 rounded-sm bg-rose-600" />
              <span>Negative Factor (-Δ)</span>
            </span>
          </div>
        </div>

        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#cbd5e1" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#334155', fontWeight: 600 }} />
              <YAxis
                type="category"
                dataKey="feature"
                tick={{ fontSize: 12, fill: '#0f172a', fontWeight: 600 }}
                width={130}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, fontSize: 12, fontWeight: 600, border: '1px solid #cbd5e1', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                formatter={(val) => [`${Number(val) > 0 ? '+' : ''}${val}`, 'SHAP Impact']}
              />
              <ReferenceLine x={0} stroke="#64748b" strokeWidth={2} />
              <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.impact >= 0 ? '#059669' : '#e11d48'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Engineering Interpretation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-300 text-xs">
          <div className="flex items-center gap-2 font-extrabold text-emerald-900 mb-1.5">
            <ArrowUpRight className="w-4 h-4 text-emerald-700" />
            <span>Key Positive Contributors</span>
          </div>
          <p className="text-slate-800 font-medium leading-relaxed">
            Pozzolanic additive reaction (silica fume / fly ash) and curing duration contribute significantly to hydration and secondary C-S-H gel formation, recovering strength loss.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 text-xs">
          <div className="flex items-center gap-2 font-extrabold text-rose-900 mb-1.5">
            <ArrowDownRight className="w-4 h-4 text-rose-700" />
            <span>Primary Restraining Constraints</span>
          </div>
          <p className="text-slate-800 font-medium leading-relaxed">
            Plastic aggregate replacement introduces weak interfacial transition zones (ITZ) and hydrophobic surfaces, which are the main downward drivers on compressive strength.
          </p>
        </div>
      </div>
    </div>
  );
};
