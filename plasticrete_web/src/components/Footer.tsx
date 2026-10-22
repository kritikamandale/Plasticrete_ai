import React from 'react';
import { useMix } from '../context/MixContext';
import { ShieldCheck, Leaf, ExternalLink, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  const { setMainRoute, setStudioTab } = useMix();

  return (
    <footer className="border-t border-slate-200/80 bg-white/70 backdrop-blur-md transition-colors mt-20 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Col 1 & 2: Brand Info */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 border border-slate-700/50 shadow-sm">
                <svg width="20" height="20" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="12" width="26" height="16" rx="2.5" fill="#3B82F6"/>
                  <path d="M16 3c-3.6 2.2-5 5.2-3.4 8.2C14 8.6 16.4 7.6 20 8c-1.6-2.6-1.6-3.4-4-5z" fill="#10B981"/>
                  <circle cx="16" cy="8.6" r="1.4" fill="#F59E0B"/>
                </svg>
              </div>
              <span className="font-extrabold text-lg text-slate-900">
                PlastiCrete<span className="text-emerald-600">.ai</span>
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-sm">
              An explainable mix studio: one recipe, one carbon number, a use-class gate, and a batch passport a lab can fill in after the cube is crushed.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-50 text-[11px] font-semibold text-emerald-700 border border-emerald-200">
                <Leaf className="w-3.5 h-3.5" />
                Circular Economy
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 text-[11px] font-semibold text-blue-700 border border-blue-200">
                <ShieldCheck className="w-3.5 h-3.5" />
                Shared mass balance
              </span>
            </div>
          </div>

          {/* Col 3: Platform Modules */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3.5">
              AI Studio Modules
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <button
                  onClick={() => { setMainRoute('studio'); setStudioTab('overview'); }}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  M1 Property Predictor
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setMainRoute('studio'); setStudioTab('optimizer'); }}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  Mix search on M1
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  Mass balance and use-class gates
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setMainRoute('studio'); setStudioTab('recommender'); }}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  M4 Application Finder & RAG
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setMainRoute('studio'); setStudioTab('explainability'); }}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  SHAP Explainability Waterfall
                </button>
              </li>
            </ul>
          </div>

          {/* Col 4: Indian Standards (BIS) */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3.5">
              Regulatory Standards
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <button
                  onClick={() => setMainRoute('standards')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  IS 15658 (Paving blocks)
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('standards')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  IS 2185 (Concrete Masonry)
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('standards')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  IS 456 (Plain & Reinforced)
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('standards')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  IS 10262 (Concrete Mix Design)
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('standards')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  IGBC / GRIHA / LEED v4.1
                </button>
              </li>
            </ul>
          </div>

          {/* Col 5: Research & Docs */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3.5">
              Science & Research
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <button
                  onClick={() => setMainRoute('technology')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  Ensemble Architecture (XGB+RF+DNN)
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('technology')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  Optuna search on the M1 ensemble
                </button>
              </li>
              <li>
                <button
                  onClick={() => setMainRoute('technology')}
                  className="hover:text-emerald-600 transition-colors cursor-pointer"
                >
                  FAISS 15D Vector RAG
                </button>
              </li>
              <li>
                <a
                  href="https://github.com/kritikamandale/Plasticrete_ai"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 hover:text-emerald-600 transition-colors"
                >
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright row */}
        <div className="pt-10 mt-10 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            © {new Date().getFullYear()} PlastiCrete AI. All civil engineering models and BIS compliance algorithms reserved.
          </div>
          <div className="flex items-center gap-2">
            <span>Built for sustainable construction innovation with</span>
            <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
          </div>
        </div>
      </div>
    </footer>
  );
};
