import React from 'react';
import { useMix, PRESETS } from '../context/MixContext';
import { FlaskConical, BookmarkCheck, RotateCcw } from 'lucide-react';

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
    <div className="glass-card rounded-2xl p-5 mb-6 border border-slate-300/80 shadow-md">
      {/* Header and Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-100 text-emerald-800">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">
              Mix Design Parameters (Input Layer)
            </h3>
            <p className="text-xs font-medium text-slate-700">
              Adjust mix proportions to trigger real-time multi-target ML inference
            </p>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2">
          <BookmarkCheck className="w-4 h-4 text-slate-700 hidden sm:block" />
          <select
            onChange={(e) => applyPreset(e.target.value)}
            className="text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-900 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm cursor-pointer"
            defaultValue=""
          >
            <option value="" disabled>Load Industry Mix Preset...</option>
            {Object.keys(PRESETS).map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <button
            onClick={() => applyPreset('M20 Eco-Standard (PET 15%)')}
            title="Reset to default mix"
            className="p-1.5 text-slate-700 hover:text-slate-900 rounded-lg hover:bg-slate-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Sliders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 pt-4">
        {/* 1. Plastic Type */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-900 flex justify-between">
            <span>Plastic Type</span>
            <span className="font-mono text-emerald-700 font-bold">{mix.plastic_type}</span>
          </label>
          <select
            value={mix.plastic_type}
            onChange={(e) => handleChange('plastic_type', e.target.value)}
            className="w-full text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-900 px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 shadow-sm cursor-pointer"
          >
            {PLASTIC_TYPES.map((pt) => (
              <option key={pt} value={pt}>{pt} Aggregate</option>
            ))}
          </select>
        </div>

        {/* 2. Replacement % */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Aggregate Replacement</span>
            <span className="font-mono text-emerald-700 font-bold">{mix.replacement_pct.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="40"
            step="0.5"
            value={mix.replacement_pct}
            onChange={(e) => handleChange('replacement_pct', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>0% (Pure Conc.)</span>
            <span>40% Max</span>
          </div>
        </div>

        {/* 3. Particle Size */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Particle Size</span>
            <span className="font-mono text-emerald-700 font-bold">{mix.particle_size_mm.toFixed(1)} mm</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="20.0"
            step="0.5"
            value={mix.particle_size_mm}
            onChange={(e) => handleChange('particle_size_mm', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>0.5 mm (Sand)</span>
            <span>20 mm (Coarse)</span>
          </div>
        </div>

        {/* 4. Water-Cement Ratio */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Water-to-Cement Ratio</span>
            <span className="font-mono text-emerald-700 font-bold">{mix.wc_ratio.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.35"
            max="0.65"
            step="0.01"
            value={mix.wc_ratio}
            onChange={(e) => handleChange('wc_ratio', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-emerald-600"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>0.35 (Dense)</span>
            <span>0.65 (Lean)</span>
          </div>
        </div>

        {/* 5. Additive Type */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-900 flex justify-between">
            <span>Pozzolanic Additive</span>
            <span className="font-mono text-cyan-800 font-bold">{mix.additive_type}</span>
          </label>
          <select
            value={mix.additive_type}
            onChange={(e) => handleChange('additive_type', e.target.value)}
            className="w-full text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-900 px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 shadow-sm cursor-pointer"
          >
            {ADDITIVE_TYPES.map((a) => (
              <option key={a.id} value={a.id}>{a.label}</option>
            ))}
          </select>
        </div>

        {/* 6. Additive % */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Additive Content</span>
            <span className="font-mono text-cyan-800 font-bold">{mix.additive_pct.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            step="0.5"
            disabled={mix.additive_type === 'none'}
            value={mix.additive_pct}
            onChange={(e) => handleChange('additive_pct', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer disabled:opacity-40 accent-cyan-600"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>0%</span>
            <span>30% Binder Mass</span>
          </div>
        </div>

        {/* 7. Curing Temp */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Curing Temperature</span>
            <span className="font-mono text-slate-900 font-bold">{mix.curing_temp_c.toFixed(0)} °C</span>
          </div>
          <input
            type="range"
            min="20"
            max="80"
            step="1"
            value={mix.curing_temp_c}
            onChange={(e) => handleChange('curing_temp_c', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-slate-700"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>20°C (Ambient)</span>
            <span>80°C (Steam)</span>
          </div>
        </div>

        {/* 8. Curing Days */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-bold text-slate-900">
            <span>Curing Age</span>
            <span className="font-mono text-slate-900 font-bold">{mix.curing_days} Days</span>
          </div>
          <input
            type="range"
            min="3"
            max="90"
            step="1"
            value={mix.curing_days}
            onChange={(e) => handleChange('curing_days', parseInt(e.target.value, 10))}
            className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-slate-700"
          />
          <div className="flex justify-between text-[11px] font-semibold text-slate-700 font-mono">
            <span>3d (Early)</span>
            <span>28d (Standard)</span>
            <span>90d (Matured)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
