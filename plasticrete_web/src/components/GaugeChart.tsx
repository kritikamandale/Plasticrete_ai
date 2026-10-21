import React from 'react';

interface GaugeChartProps {
  value: number;
  max?: number;
  label: string;
  sublabel?: string;
  grade?: string;
  size?: number;
}

export const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  max = 100,
  label,
  sublabel,
  grade,
  size = 180,
}) => {
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = Math.min(Math.max(value, 0), max);
  const strokeDashoffset = circumference - (normalizedValue / max) * circumference;

  // Determine color based on score
  let strokeColor = '#059669'; // Emerald
  if (value < 50) strokeColor = '#EF4444'; // Red
  else if (value < 70) strokeColor = '#D97706'; // Amber-600
  else if (value < 85) strokeColor = '#0284C7'; // Cyan

  return (
    <div className="flex flex-col items-center justify-center p-3">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-200"
            fill="transparent"
          />
          {/* Animated score circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>

        {/* Center label */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-extrabold font-mono text-slate-950">
            {value.toFixed(0)}
          </span>
          {grade && (
            <span className="inline-block mt-0.5 text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-900 border border-slate-300">
              Grade {grade}
            </span>
          )}
        </div>
      </div>

      <span className="mt-3 text-sm font-bold text-slate-950 text-center">
        {label}
      </span>
      {sublabel && (
        <span className="text-xs font-semibold text-slate-700 text-center mt-0.5">
          {sublabel}
        </span>
      )}
    </div>
  );
};
