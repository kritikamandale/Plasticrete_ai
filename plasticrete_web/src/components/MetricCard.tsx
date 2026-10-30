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

function formatVal(value: number | null | undefined, maxDecimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  const num = Number(value);
  // Keep clean precision for civil engineering outputs
  return num.toFixed(maxDecimals);
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
    <div className="engineering-card rounded-xl p-5 min-h-[175px] flex flex-col justify-between border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs hover:border-[#333A42]/30 transition-all">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="eyebrow-tag text-[10px] text-[#525866] uppercase tracking-wider font-semibold">
            {label}
          </span>
          {Icon && (
            <div className="p-1.5 rounded-md bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0] shrink-0">
              <Icon className="w-3.5 h-3.5" />
            </div>
          )}
        </div>

        <div className="flex items-baseline gap-1.5 my-2">
          <span className="text-3xl font-bold font-mono text-[#1E2022] tracking-tight">
            {formatVal(mean, 2)}
          </span>
          <span className="text-xs font-semibold text-[#525866] font-mono">
            {unit}
          </span>
        </div>

        <p className="text-xs text-[#525866] line-clamp-2 mb-3 leading-relaxed">
          {description}
        </p>
      </div>

      {/* 90% Prediction Interval Tag */}
      {low !== null && high !== null && low !== undefined && high !== undefined ? (
        <div className="pt-2.5 border-t border-[#E5E5E0] flex items-center justify-between text-xs font-mono gap-1">
          <span className="text-[10px] font-semibold text-[#525866] uppercase tracking-wider shrink-0">Prediction range:</span>
          <span className="text-[#2563EB] bg-[#2563EB]/8 px-2 py-0.5 rounded text-[11px] font-bold border border-[#2563EB]/20 truncate">
            [{formatVal(low, 2)} – {formatVal(high, 2)}]
          </span>
        </div>
      ) : (
        <div className="pt-2.5 border-t border-[#E5E5E0] text-[10px] text-[#525866] font-mono">
          <span>Interval unavailable</span>
        </div>
      )}
    </div>
  );
};
