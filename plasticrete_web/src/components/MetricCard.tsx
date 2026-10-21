import React from 'react';
import type { PropertyResult } from '../types';

interface MetricCardProps {
  label: string;
  propKey: string;
  unit: string;
  result?: PropertyResult;
  description: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  unit,
  result,
  description,
  icon: Icon,
}) => {
  const mean = result?.mean;
  const low = result?.ci_90_low;
  const high = result?.ci_90_high;

  return (
    <div className="glass-card rounded-xl p-4 flex flex-col justify-between border border-slate-300 shadow-sm hover:border-slate-400 transition-all">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="text-xs font-bold text-slate-900">
            {label}
          </span>
          {Icon && (
            <div className="p-1.5 rounded-lg bg-slate-200 text-slate-800">
              <Icon className="w-4 h-4" />
            </div>
          )}
        </div>

        <div className="flex items-baseline gap-1.5 my-1">
          <span className="text-3xl font-extrabold font-mono text-slate-950">
            {mean !== null && mean !== undefined ? mean : '—'}
          </span>
          <span className="text-xs font-bold text-slate-700 font-mono">
            {unit}
          </span>
        </div>

        <p className="text-xs font-medium text-slate-700 line-clamp-2 mb-3">
          {description}
        </p>
      </div>

      {/* Confidence Interval Pill */}
      {low !== null && high !== null && low !== undefined && high !== undefined && (
        <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs font-mono">
          <span className="font-semibold text-slate-700">90% CI:</span>
          <span className="text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded font-bold">
            [{low} – {high}]
          </span>
        </div>
      )}
    </div>
  );
};
