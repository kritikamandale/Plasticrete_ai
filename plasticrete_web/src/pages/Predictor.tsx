import React from 'react';
import { useMix } from '../context/MixContext';
import { MixControlPanel } from '../components/MixControlPanel';
import { MetricCard } from '../components/MetricCard';
import { TARGET_LABELS } from '../types';
import {
  Activity,
  Droplets,
  Layers,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ErrorBar,
} from 'recharts';

export const Predictor: React.FC = () => {
  const { prediction } = useMix();

  const getIcon = (key: string) => {
    switch (key) {
      case 'compressive_strength_mpa':
        return Activity;
      case 'split_tensile_mpa':
      case 'flexural_strength_mpa':
        return Zap;
      case 'slump_mm':
      case 'water_absorption_pct':
        return Droplets;
      case 'density_kgm3':
        return Layers;
      default:
        return Sparkles;
    }
  };

  const strengthData = [
    {
      name: 'Compressive',
      mean: prediction?.predictions.compressive_strength_mpa?.mean || 0,
      errorHigh: (prediction?.predictions.compressive_strength_mpa?.ci_90_high || 0) - (prediction?.predictions.compressive_strength_mpa?.mean || 0),
      errorLow: (prediction?.predictions.compressive_strength_mpa?.mean || 0) - (prediction?.predictions.compressive_strength_mpa?.ci_90_low || 0),
    },
    {
      name: 'Flexural',
      mean: prediction?.predictions.flexural_strength_mpa?.mean || 0,
      errorHigh: (prediction?.predictions.flexural_strength_mpa?.ci_90_high || 0) - (prediction?.predictions.flexural_strength_mpa?.mean || 0),
      errorLow: (prediction?.predictions.flexural_strength_mpa?.mean || 0) - (prediction?.predictions.flexural_strength_mpa?.ci_90_low || 0),
    },
    {
      name: 'Split Tensile',
      mean: prediction?.predictions.split_tensile_mpa?.mean || 0,
      errorHigh: (prediction?.predictions.split_tensile_mpa?.ci_90_high || 0) - (prediction?.predictions.split_tensile_mpa?.mean || 0),
      errorLow: (prediction?.predictions.split_tensile_mpa?.mean || 0) - (prediction?.predictions.split_tensile_mpa?.ci_90_low || 0),
    },
  ];

  return (
    <div className="space-y-6">
      <MixControlPanel />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-xl font-extrabold text-slate-950">
            M1 Multi-Target Property Predictor
          </h2>
          <p className="text-xs font-semibold text-slate-700">
            Ensemble output (XGBoost + Random Forest + PyTorch Deep Neural Network) with 90% confidence intervals
          </p>
        </div>

        {prediction?.low_coverage_targets && prediction.low_coverage_targets.length > 0 && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-100 text-amber-950 text-xs font-bold border border-amber-300">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-800" />
            <span>Target extrapolation alert: {prediction.low_coverage_targets.join(', ')}</span>
          </div>
        )}
      </div>

      {/* 7 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Object.entries(TARGET_LABELS).map(([key, meta]) => (
          <MetricCard
            key={key}
            propKey={key}
            label={meta.label}
            unit={meta.unit}
            description={meta.description}
            result={prediction?.predictions[key]}
            icon={getIcon(key)}
          />
        ))}
      </div>

      {/* Chart Section */}
      <div className="glass-card rounded-2xl p-5 border border-slate-300/80 shadow-sm">
        <div className="pb-3 border-b border-slate-200">
          <h3 className="font-bold text-slate-950 text-base">
            Strength Profile & Error Bounds (90% Confidence Intervals)
          </h3>
          <p className="text-xs font-semibold text-slate-700">
            Mean predicted values (MPa) with 5th to 95th percentile epistemic + aleatoric uncertainty bars
          </p>
        </div>

        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={strengthData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#cbd5e1" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#0f172a', fontWeight: 600 }} />
              <YAxis unit=" MPa" tick={{ fontSize: 12, fill: '#334155', fontWeight: 600 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, fontSize: 12, fontWeight: 600, border: '1px solid #cbd5e1', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                formatter={(val) => [`${val} MPa`, 'Predicted Mean']}
              />
              <Bar dataKey="mean" fill="#0284c7" radius={[6, 6, 0, 0]}>
                <ErrorBar dataKey="errorHigh" width={6} strokeWidth={2} stroke="#0f172a" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
