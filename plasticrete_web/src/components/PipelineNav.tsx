import React, { useState } from 'react';
import { useMix, type StudioSubTab } from '../context/MixContext';
import {
  Activity,
  SlidersHorizontal,
  Leaf,
  Boxes,
  HelpCircle,
  LayoutDashboard,
  Sliders,
  History,
  BookmarkCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

interface StepMeta {
  tab: StudioSubTab;
  stepNumber: string;
  title: string;
  shortDesc: string;
  icon: React.ComponentType<{ className?: string }>;
  statusKey: 'm1' | 'm2' | 'm3' | 'm4';
}

const STEPS: StepMeta[] = [
  {
    tab: 'predictor',
    stepNumber: '1',
    title: 'Predict performance',
    shortDesc: 'Seven concrete properties',
    icon: Activity,
    statusKey: 'm1',
  },
  {
    tab: 'optimizer',
    stepNumber: '2',
    title: 'Improve your mix',
    shortDesc: 'Compare candidate mixes',
    icon: SlidersHorizontal,
    statusKey: 'm2',
  },
  {
    tab: 'sustainability',
    stepNumber: '3',
    title: 'Environmental impact',
    shortDesc: 'Carbon, cost, screening',
    icon: Leaf,
    statusKey: 'm3',
  },
  {
    tab: 'recommender',
    stepNumber: '4',
    title: 'Explore applications',
    shortDesc: 'Uses and references',
    icon: Boxes,
    statusKey: 'm4',
  },
];

export const PipelineNav: React.FC = () => {
  const {
    studioTab,
    setStudioTab,
    formulationId,
    formulationName,
    formulationVersion,
    isBaseline,
    selectedCandidate,
    selectCandidate,
    pipelineState,
    setIsDrawerOpen,
    setIsHistoryOpen,
    saveCurrentFormulation,
    activeMix,
  } = useMix();

  const [savedNotice, setSavedNotice] = useState(false);

  const handleQuickSave = async () => {
    const res = await saveCurrentFormulation();
    if (res) {
      setSavedNotice(true);
      setTimeout(() => setSavedNotice(false), 3000);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-2.5 h-2.5" />
            <span>Ready</span>
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#2563EB] bg-[#2563EB]/10 px-1.5 py-0.5 rounded border border-[#2563EB]/20">
            <Clock className="w-2.5 h-2.5" />
            <span>Preparing</span>
          </span>
        );
      case 'stale':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#F97316] bg-[#FFF7ED] px-1.5 py-0.5 rounded border border-[#F97316]/30">
            <AlertTriangle className="w-2.5 h-2.5" />
            <span>Out of date</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-red-700 bg-red-50 px-1.5 py-0.5 rounded border border-red-200">
            <span>Unavailable</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#525866] bg-[#F5F5F3] px-1.5 py-0.5 rounded border border-[#E5E5E0]">
            <span>Not started</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-3">
      {/* Active Formulation Bar */}
      <div className="engineering-card rounded-xl p-3.5 bg-[#FFFFFF] border border-[#E5E5E0] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="p-2 rounded-lg bg-[#333A42] text-white">
            <BookmarkCheck className="w-4 h-4 text-[#2563EB]" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-heading font-bold text-sm text-[#1E2022]">
                {formulationName}
              </span>
              <span className="font-mono text-[10px] font-semibold px-2 py-0.5 rounded bg-[#F5F5F3] border border-[#E5E5E0] text-[#525866]">
                {formulationId} (v{formulationVersion})
              </span>
              {selectedCandidate ? (
                <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Improved mix in use
                </span>
              ) : isBaseline ? (
                <span className="eyebrow-tag text-[9px] text-[#525866] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                  Current mix
                </span>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#525866] mt-0.5 font-mono">
              <span>{activeMix.plastic_type} {activeMix.replacement_pct}%</span>
              <span>•</span>
              <span>w/c {activeMix.wc_ratio.toFixed(2)}</span>
              <span>•</span>
              <span>{activeMix.particle_size_mm} mm</span>
              <span>•</span>
              <span>{activeMix.additive_type} {activeMix.additive_pct}%</span>
              <span>•</span>
              <span>{activeMix.curing_days}d ({activeMix.curing_temp_c}°C)</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {selectedCandidate && (
            <button
              onClick={() => selectCandidate(null)}
              className="text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#525866] hover:text-[#1E2022] transition-colors cursor-pointer flex items-center gap-1"
              title="Return to the mix you entered before selecting a candidate"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Use original mix</span>
            </button>
          )}

          <button
            onClick={() => setIsDrawerOpen(true)}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] hover:bg-[#E5E5E0] text-[#1E2022] transition-colors cursor-pointer flex items-center gap-1.5"
            title="Change polymer type, replacement, water/cement ratio and curing"
          >
            <Sliders className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>Define your mix</span>
          </button>

          <button
            onClick={() => setIsHistoryOpen(true)}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#333A42] transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
            title="Open saved mixes and restore a previous version"
          >
            <History className="w-3.5 h-3.5 text-[#525866]" />
            <span>Saved mixes</span>
          </button>

          <button
            onClick={handleQuickSave}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#333A42] hover:bg-[#282E34] text-white transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
            title="Save this mix and its current results"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>{savedNotice ? 'Saved!' : 'Save'}</span>
          </button>
        </div>
      </div>

      {/* Connected M1 -> M2 -> M3 -> M4 Pipeline Navigation Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {STEPS.map((step) => {
          const Icon = step.icon;
          const isActive = studioTab === step.tab;
          const status = pipelineState[step.statusKey];

          return (
            <button
              key={step.tab}
              onClick={() => setStudioTab(step.tab)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between min-h-[76px] ${
                isActive
                  ? 'bg-[#333A42] text-white border-[#282E34] shadow-xs ring-1 ring-[#2563EB]/40'
                  : 'bg-[#FFFFFF] text-[#1E2022] border-[#E5E5E0] hover:border-[#333A42]/30 hover:bg-[#F5F5F3]'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive ? 'bg-[#2563EB] text-white' : 'bg-[#F5F5F3] text-[#2563EB] border border-[#E5E5E0]'
                    }`}
                  >
                    {step.stepNumber}
                  </span>
                  <span className={`text-xs font-heading font-bold ${isActive ? 'text-white' : 'text-[#1E2022]'}`}>
                    {step.title}
                  </span>
                </div>
                {getStatusBadge(status)}
              </div>

              <div className="flex items-center justify-between w-full text-[11px] mt-1">
                <span className={`truncate text-[10px] ${isActive ? 'text-[#E5E5E0]' : 'text-[#525866]'}`}>
                  {step.shortDesc}
                </span>
                <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#2563EB]' : 'text-[#525866]'}`} />
              </div>
            </button>
          );
        })}
      </div>

      {/* Auxiliary Studio Tabs (Overview & SHAP) */}
      <div className="flex items-center gap-2 text-xs border-b border-[#E5E5E0] pb-2 pt-1">
        <span className="eyebrow-tag text-[9px] text-[#525866] uppercase">Also in this mix:</span>
        <button
          onClick={() => setStudioTab('overview')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors cursor-pointer ${
            studioTab === 'overview'
              ? 'bg-[#333A42] text-white font-semibold'
              : 'text-[#525866] hover:text-[#1E2022]'
          }`}
        >
          <LayoutDashboard className="w-3 h-3" />
          <span>Mix summary</span>
        </button>

        <button
          onClick={() => setStudioTab('explainability')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors cursor-pointer ${
            studioTab === 'explainability'
              ? 'bg-[#333A42] text-white font-semibold'
              : 'text-[#525866] hover:text-[#1E2022]'
          }`}
        >
          <HelpCircle className="w-3 h-3 text-[#2563EB]" />
          <span>Why this prediction</span>
        </button>
      </div>
    </div>
  );
};
