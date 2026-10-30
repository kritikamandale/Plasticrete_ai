import React from 'react';
import { useMix } from '../context/MixContext';
import type { StudioSubTab } from '../routing';
import { queueAnchor, revealTarget } from '../routing';
import { ExternalLink, Scale, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  const { mainRoute, setMainRoute, setStudioTab } = useMix();

  const openStudio = (tab: StudioSubTab) => {
    setStudioTab(tab);
    window.scrollTo(0, 0);
  };

  const openStandard = (id: string) => {
    if (mainRoute === 'standards' && document.getElementById(id)) {
      revealTarget(id);
      return;
    }
    queueAnchor(id);
    setMainRoute('standards');
  };

  return (
    <footer className="border-t border-[#E5E5E0] bg-[#FFFFFF] text-[#1E2022] mt-20 relative z-10">
      {/* Pre-footer Call to Action */}
      <section className="bg-[#333A42] text-white py-14 px-4 sm:px-6 lg:px-8 border-b border-[#282E34]">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <span className="eyebrow-tag text-[10px] text-[#F97316] tracking-wider block">
              MIX WORKSPACE
            </span>
            <h2 className="text-2xl sm:text-3xl font-heading font-bold text-white tracking-tight">
              Ready to work on a mix?
            </h2>
            <p className="text-sm text-[#E5E5E0] max-w-xl leading-relaxed">
              Explore material properties, compare candidate recipes, quantify environmental trade-offs, and prepare a batch record for laboratory verification.
            </p>
          </div>
          <button
            onClick={() => openStudio('overview')}
            className="shrink-0 inline-flex items-center gap-2.5 px-6 py-3 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-heading font-bold text-xs uppercase tracking-wider transition-all shadow-sm cursor-pointer"
          >
            <span>Open mix workspace</span>
          </button>
        </div>
      </section>

      {/* Main Footer Links */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Col 1 & 2: Brand Info */}
          <div className="lg:col-span-2 space-y-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#333A42] text-white border border-[#282E34]">
                <svg width="20" height="20" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="11" width="26" height="18" rx="2" fill="#333A42" stroke="#FFFFFF" strokeWidth="1.5" />
                  <rect x="7" y="16" width="7" height="9" rx="1" fill="#2563EB" />
                  <rect x="18" y="16" width="7" height="9" rx="1" fill="#2563EB" />
                  <line x1="3" y1="11" x2="16" y2="3" stroke="#FFFFFF" strokeWidth="1.5" />
                  <line x1="29" y1="11" x2="16" y2="3" stroke="#FFFFFF" strokeWidth="1.5" />
                  <circle cx="16" cy="6" r="2" fill="#F97316" />
                </svg>
              </div>
              <span className="font-heading font-bold text-lg text-[#1E2022]">
                PlastiCrete<span className="text-[#2563EB]">.ai</span>
              </span>
            </div>

            <p className="text-xs text-[#525866] leading-relaxed max-w-sm">
              Screen a plastic-waste concrete mix, review predicted properties, and record the laboratory cube. Model methods stay in the technical details.
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0]">
                <Scale className="w-3 h-3 text-[#2563EB]" />
                Shared Mass Balance
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-[#F5F5F3] text-[#333A42] border border-[#E5E5E0]">
                <ShieldCheck className="w-3 h-3 text-[#333A42]" />
                IS Standards Gates
              </span>
            </div>
          </div>

          {/* Col 3: AI Studio Modules */}
          <div>
            <h4 className="eyebrow-tag text-[10px] text-[#1E2022] mb-3 uppercase">
              Mix workspace
            </h4>
            <ul className="space-y-2 text-xs text-[#525866]">
              <li>
                <button
                  onClick={() => openStudio('predictor')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Predict concrete performance
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStudio('optimizer')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Improve your mix
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStudio('sustainability')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Environmental impact and requirements
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStudio('recommender')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Explore applications
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setMainRoute('batch'); window.scrollTo(0, 0); }}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Mix report and batch passport
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStudio('explainability')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Why this prediction
                </button>
              </li>
            </ul>
          </div>

          {/* Col 4: Regulatory Standards */}
          <div>
            <h4 className="eyebrow-tag text-[10px] text-[#1E2022] mb-3 uppercase">
              Regulatory Standards
            </h4>
            <ul className="space-y-2 text-xs text-[#525866]">
              <li>
                <button
                  onClick={() => openStandard('is-15658')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  IS 15658: Concrete Paving Blocks
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStandard('is-2185')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  IS 2185: Masonry Units (Hollow/Solid)
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStandard('is-456')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  IS 456: Plain & Reinforced Concrete
                </button>
              </li>
              <li>
                <button
                  onClick={() => openStandard('is-10262')}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  IS 10262: Mix Proportioning Guidelines
                </button>
              </li>
            </ul>
          </div>

          {/* Col 5: Science & Research */}
          <div>
            <h4 className="eyebrow-tag text-[10px] text-[#1E2022] mb-3 uppercase">
              Science & Research
            </h4>
            <ul className="space-y-2 text-xs text-[#525866]">
              <li>
                <button
                  onClick={() => { setMainRoute('interactive'); window.scrollTo(0, 0); }}
                  className="hover:text-[#2563EB] transition-colors cursor-pointer text-left"
                >
                  Mix simulator
                </button>
              </li>
              <li>
                <a
                  href="https://github.com/kritikamandale/Plasticrete_ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-[#2563EB] transition-colors"
                >
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-3 h-3 text-[#525866]" />
                </a>
              </li>
              <li className="pt-2 text-[11px] text-[#525866] leading-relaxed">
                Empirical dataset aggregated from 40+ peer-reviewed concrete polymer investigations.
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 mt-8 border-t border-[#E5E5E0] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#525866]">
          <p>© {new Date().getFullYear()} PlastiCrete.ai. All rights reserved.</p>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span>ICE v4.1 Factors</span>
            <span>•</span>
            <span>IS 516 Testing</span>
            <span>•</span>
            <span className="text-[#333A42] font-semibold">Laboratory Verification Required</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
