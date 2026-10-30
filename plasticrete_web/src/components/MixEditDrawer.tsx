import React, { useState, useEffect } from 'react';
import { useMix, PRESETS } from '../context/MixContext';
import type { MixInput } from '../types';
import {
  X,
  Sliders,
  CheckCircle2,
  Copy,
  AlertTriangle,
  BookmarkCheck,
} from 'lucide-react';
import { FieldHelp } from './FieldHelp';

const PLASTIC_OPTIONS = [
  { value: 'PET', label: 'Polyethylene Terephthalate (PET)' },
  { value: 'HDPE', label: 'High-Density Polyethylene (HDPE)' },
  { value: 'LDPE', label: 'Low-Density Polyethylene (LDPE)' },
  { value: 'PP', label: 'Polypropylene (PP)' },
  { value: 'PVC', label: 'Polyvinyl Chloride (PVC)' },
  { value: 'Mixed', label: 'Mixed Post-Consumer Polymers' },
];

const ADDITIVE_OPTIONS = [
  { value: 'fly_ash', label: 'Fly Ash (IS 3812)' },
  { value: 'silica_fume', label: 'Silica Fume (ASTM C1240)' },
  { value: 'ggbs', label: 'GGBS Slag' },
  { value: 'metakaolin', label: 'Metakaolin' },
  { value: 'fibres', label: 'Polypropylene Fibers' },
  { value: 'none', label: 'None (Plain Portland Cement)' },
];

export const MixEditDrawer: React.FC = () => {
  const {
    isDrawerOpen,
    setIsDrawerOpen,
    mix,
    setMix,
    formulationId,
    formulationName,
    formulationVersion,
    duplicateCurrentFormulation,
  } = useMix();

  // Local draft mix inputs (does not mutate global state until confirmed)
  const [draftMix, setDraftMix] = useState<MixInput>(mix);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Sync draftMix when drawer opens or mix changes
  useEffect(() => {
    if (isDrawerOpen) {
      setDraftMix(mix);
    }
  }, [isDrawerOpen, mix]);

  if (!isDrawerOpen) return null;

  const updateDraft = <K extends keyof MixInput>(key: K, val: MixInput[K]) => {
    setDraftMix((prev) => ({ ...prev, [key]: val }));
    setSelectedPreset('');
  };

  const handleApplyPreset = (presetName: string) => {
    const p = PRESETS[presetName];
    if (p) {
      setDraftMix(p);
      setSelectedPreset(presetName);
    }
  };

  const handleApplyChanges = () => {
    setMix(draftMix);
    setIsDrawerOpen(false);
  };

  const handleSaveAsNewVersion = async () => {
    setMix(draftMix);
    await duplicateCurrentFormulation(`${formulationName} (v${formulationVersion + 1})`);
    setIsDrawerOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs transition-opacity animate-fade-in">
      {/* Drawer Overlay backdrop */}
      <div className="fixed inset-0" onClick={() => setIsDrawerOpen(false)} />

      {/* Drawer Content Panel */}
      <div className="relative z-10 w-full max-w-md bg-[#FFFFFF] h-full shadow-2xl flex flex-col border-l border-[#E5E5E0] overflow-hidden">
        {/* Drawer Header */}
        <div className="p-5 border-b border-[#E5E5E0] bg-[#F5F5F3] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-[#333A42] text-white">
              <Sliders className="w-4 h-4 text-[#2563EB]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                  Define your mix
                </h3>
                <span className="font-mono text-[10px] text-[#525866] bg-[#FFFFFF] px-1.5 py-0.5 rounded border border-[#E5E5E0]">
                  v{formulationVersion}
                </span>
              </div>
              <p className="text-[11px] text-[#525866] font-mono">
                {formulationId} · {formulationName}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsDrawerOpen(false)}
            className="p-1.5 rounded-md text-[#525866] hover:text-[#1E2022] hover:bg-[#E5E5E0] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Notice of Staleness */}
        <div className="px-5 py-2.5 bg-[#FFF7ED] border-b border-[#F97316]/20 flex items-center gap-2 text-[11px] text-[#1E2022]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#F97316] shrink-0" />
          <span>If you apply changes, previous results become out of date until a new prediction is generated. Your saved mix is not overwritten until you save it.</span>
        </div>

        {/* Drawer Body - Scrollable Form */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Quick Preset Selector */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[11px] font-semibold text-[#1E2022] flex items-center gap-1">
                <BookmarkCheck className="w-3.5 h-3.5 text-[#2563EB]" />
                Load a starting mix
              </label>
            </div>
            <select
              value={selectedPreset}
              onChange={(e) => handleApplyPreset(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
            >
              <option value="">Choose a starting mix…</option>
              {Object.keys(PRESETS).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-2 border-t border-[#E5E5E0] space-y-4">
            {/* Polymer Type */}
            <div>
              <label className="block text-[11px] font-semibold text-[#1E2022] mb-1">
                Polymer type
              </label>
              <FieldHelp>Which plastic waste is used as the replacement aggregate.</FieldHelp>
              <select
                value={draftMix.plastic_type}
                onChange={(e) => updateDraft('plastic_type', e.target.value)}
                className="w-full text-xs font-medium rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
              >
                {PLASTIC_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Replacement % */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-[#1E2022]">Aggregate replacement (%)</span>
                <span className="font-mono font-bold text-[#2563EB]">{draftMix.replacement_pct} %</span>
              </div>
              <FieldHelp>Share of natural aggregate replaced by plastic particles. Range on this form: 0–40%.</FieldHelp>
              <input
                type="range"
                min="0"
                max="40"
                step="1"
                value={draftMix.replacement_pct}
                onChange={(e) => updateDraft('replacement_pct', Number(e.target.value))}
                className="w-full accent-[#2563EB] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#525866]">
                <span>0% (Control)</span>
                <span>40% (Max)</span>
              </div>
            </div>

            {/* w/c ratio */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-[#1E2022]">Water/cement ratio</span>
                <span className="font-mono font-bold text-[#2563EB]">{draftMix.wc_ratio.toFixed(2)}</span>
              </div>
              <FieldHelp>Mass of mixing water divided by cementitious binder. Range on this form: 0.35–0.65.</FieldHelp>
              <input
                type="range"
                min="0.35"
                max="0.65"
                step="0.01"
                value={draftMix.wc_ratio}
                onChange={(e) => updateDraft('wc_ratio', Number(e.target.value))}
                className="w-full accent-[#2563EB] cursor-pointer"
              />
            </div>

            {/* Particle size */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-[#1E2022]">Particle size (mm)</span>
                <span className="font-mono font-bold text-[#2563EB]">{draftMix.particle_size_mm} mm</span>
              </div>
              <FieldHelp>Nominal size of the plastic particles. Range on this form: 0.5–12 mm.</FieldHelp>
              <input
                type="range"
                min="0.5"
                max="12"
                step="0.5"
                value={draftMix.particle_size_mm}
                onChange={(e) => updateDraft('particle_size_mm', Number(e.target.value))}
                className="w-full accent-[#2563EB] cursor-pointer"
              />
            </div>

            {/* Mineral Additive */}
            <div>
              <label className="block text-[11px] font-semibold text-[#1E2022] mb-1">
                Mineral additive
              </label>
              <FieldHelp>Optional supplementary cementitious material or fibre in the binder.</FieldHelp>
              <select
                value={draftMix.additive_type}
                onChange={(e) => updateDraft('additive_type', e.target.value)}
                className="w-full text-xs font-medium rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB] cursor-pointer"
              >
                {ADDITIVE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Additive Dosage */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-[#1E2022]">Additive dosage (%)</span>
                <span className="font-mono font-bold text-[#2563EB]">{draftMix.additive_pct} %</span>
              </div>
              <FieldHelp>Share of the binder replaced or supplemented by the additive. Range on this form: 0–30%.</FieldHelp>
              <input
                type="range"
                min="0"
                max="30"
                step="1"
                value={draftMix.additive_pct}
                onChange={(e) => updateDraft('additive_pct', Number(e.target.value))}
                className="w-full accent-[#2563EB] cursor-pointer"
              />
            </div>

            {/* Curing Age & Temp */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Curing age (days)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{draftMix.curing_days} d</span>
                </div>
                <FieldHelp>Age at which properties are predicted. Range: 3–90 days.</FieldHelp>
                <input
                  type="range"
                  min="3"
                  max="90"
                  step="1"
                  value={draftMix.curing_days}
                  onChange={(e) => updateDraft('curing_days', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#1E2022]">Curing temperature (°C)</span>
                  <span className="font-mono font-bold text-[#2563EB]">{draftMix.curing_temp_c} °C</span>
                </div>
                <FieldHelp>Curing temperature used for the prediction. Range: 10–60 °C.</FieldHelp>
                <input
                  type="range"
                  min="10"
                  max="60"
                  step="1"
                  value={draftMix.curing_temp_c}
                  onChange={(e) => updateDraft('curing_temp_c', Number(e.target.value))}
                  className="w-full accent-[#2563EB] cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-[#E5E5E0] bg-[#F5F5F3] space-y-2">
          <button
            onClick={handleApplyChanges}
            className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-heading font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-xs"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Use this mix</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleSaveAsNewVersion}
              className="inline-flex items-center justify-center gap-1.5 py-2 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-xs font-semibold text-[#333A42] transition-colors cursor-pointer shadow-xs"
              title="Duplicate formulation as next version"
            >
              <Copy className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>Save as v{formulationVersion + 1}</span>
            </button>

            <button
              onClick={() => {
                setDraftMix(mix);
                setIsDrawerOpen(false);
              }}
              className="inline-flex items-center justify-center gap-1.5 py-2 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-xs font-semibold text-[#525866] transition-colors cursor-pointer"
            >
              <span>Cancel</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
