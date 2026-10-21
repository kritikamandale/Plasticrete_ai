import React from 'react';
import { useMix, type MainNavRoute } from '../context/MixContext';
import { Sparkles, ArrowRight, ShieldCheck, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { mainRoute, setMainRoute, score, loading } = useMix();

  const navLinks: { id: MainNavRoute; label: string; badge?: string }[] = [
    { id: 'home', label: 'Home' },
    { id: 'studio', label: 'AI Studio', badge: 'Interactive' },
    { id: 'standards', label: 'BIS Standards' },
    { id: 'technology', label: 'ML Architecture' },
  ];

  return (
    <header className="sticky top-0 z-50 w-full glass-nav transition-all">
      <div className="max-w-7xl mx-auto flex h-20 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <button
          onClick={() => setMainRoute('home')}
          className="flex items-center gap-3 group text-left cursor-pointer"
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-slate-900 via-slate-800 to-emerald-950 shadow-md border border-slate-700/30 group-hover:shadow-emerald-500/10 group-hover:border-emerald-500/30 transition-all">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="12" width="26" height="16" rx="2.5" fill="#3B82F6"/>
              <rect x="7" y="16" width="7" height="8" rx="1" fill="#1E40AF"/>
              <rect x="18" y="16" width="7" height="8" rx="1" fill="#1E40AF"/>
              <path d="M16 3c-3.6 2.2-5 5.2-3.4 8.2C14 8.6 16.4 7.6 20 8c-1.6-2.6-1.6-3.4-4-5z" fill="#10B981"/>
              <circle cx="16" cy="8.6" r="1.4" fill="#F59E0B"/>
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight text-slate-900">
                PlastiCrete<span className="text-emerald-600">.ai</span>
              </span>
              <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                Civil DeepTech
              </span>
            </div>
            <p className="text-xs text-slate-700 font-semibold hidden sm:block">
              Waste Plastic Composite Concrete Engineering
            </p>
          </div>
        </button>

        {/* Website Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-200/80 p-1.5 rounded-2xl border border-slate-300/80">
          {navLinks.map((link) => {
            const isActive = mainRoute === link.id;
            return (
              <button
                key={link.id}
                onClick={() => setMainRoute(link.id)}
                className={`relative px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white text-slate-950 shadow-sm border border-slate-300'
                    : 'text-slate-800 hover:text-slate-950 hover:bg-white/60'
                }`}
              >
                <span>{link.label}</span>
                {link.badge && (
                  <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-100 text-emerald-900">
                    {link.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Header Right Actions */}
        <div className="flex items-center gap-3">
          {/* Real-time Indicator */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 font-bold shadow-sm">
            <span className="flex h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
            <span className="font-bold text-[11px] text-slate-800">
              {loading ? 'Evaluating...' : 'Models Ready'}
            </span>
            <span className="text-slate-400">|</span>
            <span className="text-emerald-800 font-bold text-[11px] flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
              {score?.bis_overall_pass ? 'IS 1237 Compliant' : 'Review Needed'}
            </span>
          </div>

          {/* Primary CTA Button */}
          {mainRoute !== 'studio' ? (
            <button
              onClick={() => setMainRoute('studio')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-emerald-700 text-white font-bold text-xs tracking-wide shadow-md hover:shadow-emerald-500/20 transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Launch Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={() => setMainRoute('home')}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs border border-slate-300 shadow-sm transition-all cursor-pointer"
            >
              <Activity className="w-3.5 h-3.5 text-emerald-700" />
              <span>Back to Home</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
