import React from 'react';
import { useMix, type StudioSubTab } from '../context/MixContext';
import {
  LayoutDashboard,
  SlidersHorizontal,
  Leaf,
  Boxes,
  HelpCircle,
} from 'lucide-react';

interface NavItem {
  id: StudioSubTab;
  label: string;
  badge?: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Studio Overview', icon: LayoutDashboard },
  { id: 'optimizer', label: 'M2 Pareto Optimizer', icon: SlidersHorizontal, badge: 'Optuna' },
  { id: 'sustainability', label: 'M3 Carbon & BIS Scorer', icon: Leaf, badge: 'LCA' },
  { id: 'recommender', label: 'M4 Application Finder', icon: Boxes, badge: 'RAG' },
  { id: 'explainability', label: 'SHAP Explainability', icon: HelpCircle },
];

export const Sidebar: React.FC = () => {
  const { studioTab, setStudioTab } = useMix();

  return (
    <aside className="w-64 flex-shrink-0 border-r border-slate-300 bg-white flex flex-col justify-between p-4 transition-colors">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-xs font-bold uppercase tracking-wider text-slate-800 mb-2">
            Intelligence Modules
          </p>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = studioTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setStudioTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl font-bold text-sm transition-all cursor-pointer ${
                    isActive
                      ? 'bg-emerald-100 text-emerald-950 shadow-sm border border-emerald-300'
                      : 'text-slate-800 hover:bg-slate-100 hover:text-slate-950'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-700' : 'text-slate-700'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-mono font-bold ${
                      isActive
                        ? 'bg-emerald-200 text-emerald-950'
                        : 'bg-slate-200 text-slate-900'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 rounded-xl bg-slate-100 border border-slate-300 text-xs text-slate-800 space-y-1.5">
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-slate-700 font-semibold">Target Standard:</span>
          <span className="text-slate-950 font-bold">IS 10262 / 1237</span>
        </div>
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-slate-700 font-semibold">Baseline Concrete:</span>
          <span className="text-slate-950 font-bold">M20 Conventional</span>
        </div>
        <div className="pt-1.5 border-t border-slate-300 flex items-center justify-between text-[11px] text-slate-700 font-semibold">
          <span>Inference Latency</span>
          <span className="text-emerald-800 font-bold">&lt; 15ms</span>
        </div>
      </div>
    </aside>
  );
};
