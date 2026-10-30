import React from 'react';
import { useMix } from '../context/MixContext';
import {
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  Home,
  AlertTriangle,
} from 'lucide-react';

export const StandardsPage: React.FC = () => {
  const { setMainRoute, setStudioTab } = useMix();

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-4">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-[#525866] font-semibold">
        <button
          onClick={() => setMainRoute('home')}
          className="flex items-center gap-1 hover:text-[#1E2022] transition-colors cursor-pointer"
        >
          <Home className="w-3.5 h-3.5" />
          <span>Home</span>
        </button>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-[#1E2022] font-bold">Regulatory Standards & Compliance</span>
      </div>

      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#F5F5F3] border border-[#E5E5E0] text-[#333A42] text-[11px] font-mono mb-3">
          <ShieldCheck className="w-3.5 h-3.5 text-[#2563EB]" />
          <span className="font-bold uppercase tracking-wider text-[10px]">
            Screening requirements
          </span>
        </div>
        <h1 className="text-3xl font-heading font-bold text-[#1E2022] tracking-tight">
          Indian Standards a Mix Can Be Screened Against
        </h1>
        <p className="text-xs sm:text-sm text-[#525866] mt-2 max-w-3xl leading-relaxed">
          Each candidate product is evaluated against its corresponding Indian standard using the conservative lower bound of the 90% prediction interval. Screening clearance indicates eligibility for trial casting; physical IS 516 cube testing is required for certified compliance.
        </p>
      </div>

      {/* Standards Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* IS 15658 */}
        <div id="is-15658" className="engineering-card scroll-mt-24 rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <span className="font-mono text-xs font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                IS 15658
              </span>
              <span className="eyebrow-tag text-[9px] text-[#525866]">PAVER GATE</span>
            </div>
            <h3 className="font-heading font-bold text-[#1E2022] text-base mb-1.5">
              Concrete Paving Blocks
            </h3>
            <p className="text-xs text-[#525866] leading-relaxed mb-4">
              Precast concrete paving units for residential, commercial and light industrial pavements.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Min Compressive:</span>
                <span className="font-bold text-[#1E2022]">≥ 30.0 MPa</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Max Water Absorption:</span>
                <span className="font-bold text-[#1E2022]">≤ 6.0%</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Verification Gate:</span>
                <span className="font-bold text-[#2563EB]">Cast 28d Batch</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* IS 2185 */}
        <div id="is-2185" className="engineering-card scroll-mt-24 rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                IS 2185 (Part 1)
              </span>
              <span className="eyebrow-tag text-[9px] text-[#525866]">MASONRY GATE</span>
            </div>
            <h3 className="font-heading font-bold text-[#1E2022] text-base mb-1.5">
              Concrete Masonry Units
            </h3>
            <p className="text-xs text-[#525866] leading-relaxed mb-4">
              Solid and hollow concrete blocks for load-bearing and non-load-bearing masonry partition walls.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Min Compressive:</span>
                <span className="font-bold text-[#1E2022]">≥ 5.0 MPa</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Max Dry Density:</span>
                <span className="font-bold text-[#1E2022]">≤ 1800 kg/m³</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Max Water Absorption:</span>
                <span className="font-bold text-[#1E2022]">≤ 10.0%</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* IS 456 */}
        <div id="is-456" className="engineering-card scroll-mt-24 rounded-xl p-6 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div id="is-10262" className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3 scroll-mt-24">
              <span className="font-mono text-xs font-bold text-[#333A42] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                IS 456 & 10262
              </span>
              <span className="eyebrow-tag text-[9px] text-[#525866]">STRUCTURAL GATE</span>
            </div>
            <h3 className="font-heading font-bold text-[#1E2022] text-base mb-1.5">
              Plain & Reinforced Concrete
            </h3>
            <p className="text-xs text-[#525866] leading-relaxed mb-4">
              Structural concrete elements. Plastic aggregate replacement is restricted to non-structural or experimental applications.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Min Structural Grade:</span>
                <span className="font-bold text-[#1E2022]">M20 / M25</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Max Plastic Volume:</span>
                <span className="font-bold text-[#F97316]">≤ 15.0% Rec.</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-[#F5F5F3] border border-[#E5E5E0]">
                <span className="text-[#525866]">Approval Path:</span>
                <span className="font-bold text-[#1E2022]">Site Engineer Hold</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-[#E5E5E0] text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Standards Disclaimer Banner */}
      <div className="rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] p-5 shadow-xs flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-[#F97316] shrink-0 mt-0.5" />
        <div className="text-xs text-[#525866] leading-relaxed">
          <strong className="text-[#1E2022] block font-heading text-sm mb-1">
            Certification & Regulatory Disclaimer
          </strong>
          Screening candidate formulations through PlastiCrete.ai does not constitute official certification by the Bureau of Indian Standards (BIS) or statutory building authorities. Output data serves as an algorithmic decision-support tool. Production deployment mandates certified independent laboratory verification per IS 516 protocols.
        </div>
      </div>
    </div>
  );
};
