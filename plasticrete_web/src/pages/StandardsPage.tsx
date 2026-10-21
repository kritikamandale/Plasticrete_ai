import React from 'react';
import { useMix } from '../context/MixContext';
import {
  ShieldCheck,
  Award,
  ArrowRight,
  ChevronRight,
  Home,
} from 'lucide-react';

export const StandardsPage: React.FC = () => {
  const { setMainRoute, setStudioTab } = useMix();

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-4">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-slate-800 font-bold">
        <button
          onClick={() => setMainRoute('home')}
          className="flex items-center gap-1 hover:text-slate-950 transition-colors cursor-pointer"
        >
          <Home className="w-4 h-4 text-slate-700" />
          <span>Home</span>
        </button>
        <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
        <span className="text-slate-950 font-extrabold">Regulatory Standards & Compliance</span>
      </div>

      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-950 text-xs font-bold border border-emerald-300 mb-3">
          <ShieldCheck className="w-4 h-4 text-emerald-800" />
          <span>National Building Code & BIS Compliance Matrix</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-950 tracking-tight">
          Indian Standards & Green Certification Benchmarks
        </h1>
        <p className="text-sm font-semibold text-slate-800 mt-2 max-w-3xl leading-relaxed">
          PlastiCrete AI incorporates deterministic regulatory rules from the Bureau of Indian Standards (BIS) and green building rating systems (IGBC, GRIHA, LEED v4.1) directly into its multi-objective evaluation pipeline.
        </p>
      </div>

      {/* Standards Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* IS 1237 */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
              <span className="font-mono text-xs font-bold text-emerald-900 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-200">
                IS 1237:2012
              </span>
              <span className="text-xs text-slate-700 font-bold">BIS Certified</span>
            </div>
            <h3 className="font-extrabold text-slate-950 text-base mb-1.5">
              Cement Concrete Flooring Tiles & Pavers
            </h3>
            <p className="text-xs font-medium text-slate-800 leading-relaxed mb-4">
              Specifies the physical and mechanical requirements for precast cement concrete flooring tiles and heavy pedestrian paving blocks.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Min. Compressive:</span>
                <span className="font-extrabold text-slate-950">&gt;= 30.0 MPa</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Max. Water Absorption:</span>
                <span className="font-extrabold text-slate-950">&lt;= 10.0%</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Wear Resistance:</span>
                <span className="font-extrabold text-slate-950">&lt;= 2.0 mm (Class AA)</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-slate-200 text-xs font-bold text-emerald-800 flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify current mix in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* IS 2185 */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
              <span className="font-mono text-xs font-bold text-blue-900 bg-blue-100 px-2.5 py-0.5 rounded border border-blue-200">
                IS 2185 (Part 1 & 2)
              </span>
              <span className="text-xs text-slate-700 font-bold">BIS Certified</span>
            </div>
            <h3 className="font-extrabold text-slate-950 text-base mb-1.5">
              Concrete Masonry Units (Hollow & Solid)
            </h3>
            <p className="text-xs font-medium text-slate-800 leading-relaxed mb-4">
              Governs precast load-bearing and non-load-bearing masonry blocks, hollow lightweight partitions, and structural infill.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Min. CS (Grade A):</span>
                <span className="font-extrabold text-slate-950">&gt;= 5.0 MPa</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Min. Dry Density:</span>
                <span className="font-extrabold text-slate-950">&gt;= 1800 kg/m³</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Drying Shrinkage:</span>
                <span className="font-extrabold text-slate-950">&lt;= 0.06%</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-slate-200 text-xs font-bold text-blue-800 flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify current mix in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* IS 456 */}
        <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
              <span className="font-mono text-xs font-bold text-indigo-900 bg-indigo-100 px-2.5 py-0.5 rounded border border-indigo-200">
                IS 456:2000
              </span>
              <span className="text-xs text-slate-700 font-bold">BIS Structural</span>
            </div>
            <h3 className="font-extrabold text-slate-950 text-base mb-1.5">
              Plain and Reinforced Structural Concrete
            </h3>
            <p className="text-xs font-medium text-slate-800 leading-relaxed mb-4">
              Code of practice for general structural concrete design, defining characteristic compressive strength bands from M15 to M60.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Min. Grade (PCC):</span>
                <span className="font-extrabold text-slate-950">M15 (15.0 MPa)</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Min. Grade (RCC):</span>
                <span className="font-extrabold text-slate-950">M20 (20.0 MPa)</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-slate-700 font-semibold">Max. Free W/C Ratio:</span>
                <span className="font-extrabold text-slate-950">&lt;= 0.50 (Moderate)</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => { setMainRoute('studio'); setStudioTab('sustainability'); }}
            className="mt-6 pt-3 border-t border-slate-200 text-xs font-bold text-indigo-800 flex items-center gap-1 cursor-pointer hover:gap-1.5 transition-all"
          >
            <span>Verify current mix in Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Green Rating Points Matrix */}
      <div className="glass-card rounded-2xl p-6 border border-slate-300 shadow-sm">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-200">
          <Award className="w-5 h-5 text-emerald-700" />
          <div>
            <h3 className="font-bold text-slate-950 text-base">
              Green Building Rating Frameworks
            </h3>
            <p className="text-xs font-semibold text-slate-700">
              Credit criteria integrated into the M3 scoring engine
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 space-y-2">
            <span className="font-bold text-slate-950 block text-sm">IGBC Green New Buildings</span>
            <p className="text-slate-800 font-medium leading-relaxed">
              <strong>Credit MR 3: Recycled Content.</strong> Awards up to 3 credits for replacing virgin stone aggregate with certified post-consumer plastic waste (&gt;50 kg/m³ diversion).
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 space-y-2">
            <span className="font-bold text-slate-950 block text-sm">GRIHA v2019 (TERI / MNRE)</span>
            <p className="text-slate-800 font-medium leading-relaxed">
              <strong>Criterion 17: Low-Embodied Carbon Materials.</strong> Up to 2 points for &gt;10% reduction in cradle-to-gate embodied energy vs conventional M20 concrete.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 space-y-2">
            <span className="font-bold text-slate-950 block text-sm">LEED v4.1 (USGBC / GBCI)</span>
            <p className="text-slate-800 font-medium leading-relaxed">
              <strong>MR Credit: Building Product Disclosure & Optimization.</strong> Environmental Product Declaration (EPD) alignment and circular feedstock diversion points.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
