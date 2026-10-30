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
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = Math.min(Math.max(value, 0), max);
  const strokeDashoffset = circumference - (normalizedValue / max) * circumference;

  // Concrete & Composite Theme: Blue for high, structural dark for neutral, orange for warning/low
  let strokeColor = '#2563EB'; // Polymer Blue
  if (value < 45) strokeColor = '#F97316'; // Safety Orange warning
  else if (value < 70) strokeColor = '#333A42'; // Structural Dark

  return (
    <div className="flex flex-col items-center justify-center p-3">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#E5E5E0"
            strokeWidth={strokeWidth}
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
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-bold font-mono text-[#1E2022] tracking-tight">
            {Math.round(normalizedValue)}
          </span>
          <span className="text-[10px] uppercase font-bold text-[#525866] font-mono tracking-wider">
            / {max}
          </span>
          {grade && (
            <span className="mt-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-[#333A42] text-white">
              Grade {grade}
            </span>
          )}
        </div>
      </div>

      {label && (
        <span className="mt-3 font-heading font-semibold text-[#1E2022] text-xs text-center">
          {label}
        </span>
      )}
      {sublabel && (
        <span className="text-[11px] text-[#525866] text-center max-w-[200px] mt-0.5 leading-snug">
          {sublabel}
        </span>
      )}
    </div>
  );
};
