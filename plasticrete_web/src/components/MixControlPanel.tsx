import React from 'react';
import { useMix, PRESETS } from '../context/MixContext';
import { FlaskConical, BookmarkCheck, RotateCcw, ChevronDown } from 'lucide-react';

const PLASTIC_TYPES = ['PET', 'HDPE', 'LDPE', 'PVC', 'PP', 'Mixed'];
const ADDITIVE_TYPES = [
  { id: 'none', label: 'None' },
  { id: 'fly_ash', label: 'Fly Ash (IS 3812)' },
  { id: 'silica_fume', label: 'Silica Fume (IS 15388)' },
  { id: 'fibres', label: 'Recycled PP Fibres' },
];

export const MixControlPanel: React.FC = () => {
  const { mix, setMix, applyPreset } = useMix();

  const handleChange = (key: keyof typeof mix, value: string | number) => {
    setMix((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <div className="engineering-card rounded-xl p-5 mb-6 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
      {/* Structural Header with Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E0]">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-[#333A42] text-white">
            <FlaskConical className="w-4 h-4 text-[#2563EB]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-heading font-bold text-[#1E2022] text-sm tracking-tight">
                Define your mix
              </h3>
            </div>
            <p className="text-xs text-[#525866]">
              Change the mix proportions. A new prediction is generated from these inputs.
            </p>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2">
          <BookmarkCheck className="w-4 h-4 text-[#525866] hidden sm:block" />
          <div className="relative">
            <select
              onChange={(e) => applyPreset(e.target.value)}
              className="text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] text-[#1E2022] px-3 py-1.5 pr-8 focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer appearance-none"
              defaultValue=""
            >
              <option value="" disabled>Load a starting mix…</option>
              {Object.keys(PRESETS).map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#525866] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
          <button
            onClick={() => applyPreset('M20 Eco-Standard (PET 15%)')}
            title="Reset to default mix"
            className="p-1.5 text-[#525866] hover:text-[#1E2022] rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Sliders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 pt-4">
        {/* 1. Plastic Type */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#1E2022] flex justify-between">
            <span className="text-[#525866]">Polymer Type</span>
            <span className="font-mono text-[#2563EB] font-bold">{mix.plastic_type}</span>
          </label>
          <div className="relative">
            <select
              value={mix.plastic_type}
              onChange={(e) => handleChange('plastic_type', e.target.value)}
              className="w-full text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] text-[#1E2022] px-2.5 py-1.5 pr-7 focus:ring-2 focus:ring-[#2563EB] appearance-none cursor-pointer"
            >
              {PLASTIC_TYPES.map((pt) => (
                <option key={pt} value={pt}>{pt} Polymer Aggregate</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#525866] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* 2. Replacement % */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">Aggregate Replacement</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.replacement_pct}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="40"
            step="1"
            value={mix.replacement_pct}
            onChange={(e) => handleChange('replacement_pct', parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>0% (Control)</span>
            <span>40% (Max)</span>
          </div>
        </div>

        {/* 3. Water-Cement Ratio */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">w/c Ratio</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.wc_ratio}</span>
          </div>
          <input
            type="range"
            min="0.30"
            max="0.65"
            step="0.01"
            value={mix.wc_ratio}
            onChange={(e) => handleChange('wc_ratio', parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>0.30 (Dry)</span>
            <span>0.65 (High)</span>
          </div>
        </div>

        {/* 4. Particle Size (mm) */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">Particle Size</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.particle_size_mm} mm</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="12.0"
            step="0.5"
            value={mix.particle_size_mm}
            onChange={(e) => handleChange('particle_size_mm', parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>0.5 mm (Flakes)</span>
            <span>12 mm (Pellets)</span>
          </div>
        </div>

        {/* 5. Mineral Additive */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[#1E2022] flex justify-between">
            <span className="text-[#525866]">Mineral Additive</span>
            <span className="font-mono text-[#1E2022] font-bold text-[11px] truncate max-w-[120px]">
              {ADDITIVE_TYPES.find((a) => a.id === mix.additive_type)?.label || mix.additive_type}
            </span>
          </label>
          <div className="relative">
            <select
              value={mix.additive_type}
              onChange={(e) => handleChange('additive_type', e.target.value)}
              className="w-full text-xs font-semibold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] text-[#1E2022] px-2.5 py-1.5 pr-7 focus:ring-2 focus:ring-[#2563EB] appearance-none cursor-pointer"
            >
              {ADDITIVE_TYPES.map((a) => (
                <option key={a.id} value={a.id}>{a.label}</option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#525866] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* 6. Additive % */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">Additive Dosage</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.additive_pct}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            step="1"
            value={mix.additive_pct}
            onChange={(e) => handleChange('additive_pct', parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>0%</span>
            <span>30%</span>
          </div>
        </div>

        {/* 7. Curing Days */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">Curing Age</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.curing_days} Days</span>
          </div>
          <input
            type="range"
            min="3"
            max="90"
            step="1"
            value={mix.curing_days}
            onChange={(e) => handleChange('curing_days', parseInt(e.target.value, 10))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>7d (Early)</span>
            <span>28d (Standard)</span>
            <span>90d (Full)</span>
          </div>
        </div>

        {/* 8. Curing Temp */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-[#525866]">Curing Temp</span>
            <span className="font-mono text-[#1E2022] font-bold">{mix.curing_temp_c} °C</span>
          </div>
          <input
            type="range"
            min="10"
            max="60"
            step="1"
            value={mix.curing_temp_c}
            onChange={(e) => handleChange('curing_temp_c', parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#E5E5E0] rounded-lg appearance-none cursor-pointer accent-[#2563EB]"
          />
          <div className="flex justify-between text-[10px] font-mono text-[#525866]">
            <span>10°C (Cold)</span>
            <span>27°C (IS 516)</span>
            <span>60°C (Steam)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
