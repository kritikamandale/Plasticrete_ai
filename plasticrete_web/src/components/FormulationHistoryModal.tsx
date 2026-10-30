import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import {
  X,
  History,
  Search,
  RotateCcw,
  Trash2,
  Scale,
} from 'lucide-react';

export const FormulationHistoryModal: React.FC = () => {
  const {
    isHistoryOpen,
    setIsHistoryOpen,
    savedFormulations,
    restoreSavedFormulation,
    removeSavedFormulation,
    formulationId,
  } = useMix();

  const [search, setSearch] = useState('');
  const [compareIdA, setCompareIdA] = useState<string | null>(null);
  const [compareIdB, setCompareIdB] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'compare'>('list');

  if (!isHistoryOpen) return null;

  const filtered = savedFormulations.filter((f) => {
    const q = search.toLowerCase();
    return (
      f.name.toLowerCase().includes(q) ||
      f.id.toLowerCase().includes(q) ||
      f.mix_params?.plastic_type?.toLowerCase().includes(q)
    );
  });

  const recordA = savedFormulations.find((f) => f.id === compareIdA);
  const recordB = savedFormulations.find((f) => f.id === compareIdB);

  const startCompare = (id: string) => {
    if (!compareIdA) {
      setCompareIdA(id);
    } else if (!compareIdB && compareIdA !== id) {
      setCompareIdB(id);
      setViewMode('compare');
    } else {
      setCompareIdA(id);
      setCompareIdB(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs transition-opacity animate-fade-in">
      {/* Modal Dialog Card */}
      <div className="relative z-10 w-full max-w-4xl bg-[#FFFFFF] rounded-2xl shadow-2xl border border-[#E5E5E0] flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[#E5E5E0] bg-[#F5F5F3] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#333A42] text-white">
              <History className="w-5 h-5 text-[#2563EB]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-heading font-bold text-base text-[#1E2022]">
                  Saved mixes
                </h2>
                <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#E5E5E0] text-[#525866]">
                  {savedFormulations.length} Records
                </span>
              </div>
              <p className="text-xs text-[#525866]">
                Restore a saved mix. If the mix inputs have changed since the last prediction, results will be marked out of date.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex rounded-lg bg-[#E5E5E0]/70 p-1 text-xs font-semibold">
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                  viewMode === 'list' ? 'bg-[#333A42] text-white' : 'text-[#525866]'
                }`}
              >
                Browse Records
              </button>
              <button
                onClick={() => setViewMode('compare')}
                disabled={!compareIdA || !compareIdB}
                className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                  viewMode === 'compare'
                    ? 'bg-[#333A42] text-white'
                    : 'text-[#525866] disabled:opacity-40'
                }`}
              >
                Side-by-Side Compare
              </button>
            </div>

            <button
              onClick={() => setIsHistoryOpen(false)}
              className="p-1.5 rounded-lg text-[#525866] hover:text-[#1E2022] hover:bg-[#E5E5E0] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Search & Selection Filter Bar */}
        {viewMode === 'list' && (
          <div className="px-5 py-3 border-b border-[#E5E5E0] bg-[#FFFFFF] flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-[#525866] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by ID, name, polymer..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full text-xs rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] pl-9 pr-3 py-2 text-[#1E2022] focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              />
            </div>

            {compareIdA && (
              <div className="text-xs text-[#525866] flex items-center gap-2 font-mono">
                <span>Selected for Compare:</span>
                <span className="font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                  {compareIdA}
                </span>
                {compareIdB ? (
                  <>
                    <span>vs</span>
                    <span className="font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                      {compareIdB}
                    </span>
                    <button
                      onClick={() => setViewMode('compare')}
                      className="text-[#2563EB] hover:underline font-bold"
                    >
                      Compare Now →
                    </button>
                  </>
                ) : (
                  <span>(Click second mix to compare)</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {viewMode === 'list' ? (
            filtered.length === 0 ? (
              <div className="py-16 text-center">
                <History className="w-10 h-10 text-[#525866]/40 mx-auto mb-3" />
                <h4 className="font-heading font-bold text-sm text-[#1E2022]">No saved formulations found</h4>
                <p className="text-xs text-[#525866] max-w-sm mx-auto mt-1">
                  Save the mix you are working on, or load a starting mix, then save it here.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filtered.map((record) => {
                  const isCurrent = record.id === formulationId;
                  const isCompA = compareIdA === record.id;
                  const isCompB = compareIdB === record.id;
                  const cs = record.prediction?.predictions?.compressive_strength_mpa?.mean;
                  const co2 = record.score?.co2_saving_pct;

                  return (
                    <div
                      key={record.id}
                      className={`p-4 rounded-xl border transition-all ${
                        isCurrent
                          ? 'bg-[#2563EB]/5 border-[#2563EB]/40 ring-1 ring-[#2563EB]/20'
                          : 'bg-[#FFFFFF] border-[#E5E5E0] hover:border-[#333A42]/30'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-heading font-bold text-sm text-[#1E2022]">
                              {record.name}
                            </h4>
                            <span className="font-mono text-[10px] text-[#525866] bg-[#F5F5F3] px-2 py-0.5 rounded border border-[#E5E5E0]">
                              {record.id} (v{record.version})
                            </span>
                            {isCurrent && (
                              <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                                In use
                              </span>
                            )}
                            {record.status === 'stale' && (
                              <span className="eyebrow-tag text-[9px] text-[#F97316] bg-[#FFF7ED] px-2 py-0.5 rounded border border-[#F97316]/30">
                                Out of date
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#525866] font-mono mt-1">
                            <span>{record.mix_params?.plastic_type} {record.mix_params?.replacement_pct}%</span>
                            <span>•</span>
                            <span>w/c {record.mix_params?.wc_ratio}</span>
                            <span>•</span>
                            <span>{record.mix_params?.particle_size_mm} mm</span>
                            <span>•</span>
                            <span>{record.mix_params?.additive_type} {record.mix_params?.additive_pct}%</span>
                            <span>•</span>
                            <span>Updated: {new Date(record.updated_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        {/* Summary Badges & Actions */}
                        <div className="flex flex-wrap items-center gap-2">
                          {cs != null && (
                            <span className="px-2 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] text-[11px] font-mono font-bold text-[#1E2022]">
                              {cs.toFixed(1)} MPa
                            </span>
                          )}
                          {co2 != null && (
                            <span className="px-2 py-1 rounded bg-emerald-50 border border-emerald-200 text-[11px] font-mono font-bold text-emerald-800">
                              -{co2.toFixed(0)}% CO₂
                            </span>
                          )}

                          <button
                            onClick={() => startCompare(record.id)}
                            className={`text-xs font-semibold px-2.5 py-1.5 rounded-lg border transition-colors cursor-pointer flex items-center gap-1 ${
                              isCompA || isCompB
                                ? 'bg-[#333A42] text-white border-[#333A42]'
                                : 'border-[#E5E5E0] bg-[#FFFFFF] text-[#333A42] hover:bg-[#F5F5F3]'
                            }`}
                            title="Select to compare against another formulation"
                          >
                            <Scale className="w-3.5 h-3.5" />
                            <span>{isCompA ? 'Comp #1' : isCompB ? 'Comp #2' : 'Compare'}</span>
                          </button>

                          <button
                            onClick={() => restoreSavedFormulation(record)}
                            disabled={isCurrent}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 shadow-xs"
                            title="Restore this formulation as active mix"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            <span>Restore</span>
                          </button>

                          <button
                            onClick={() => removeSavedFormulation(record.id)}
                            className="p-1.5 rounded-lg text-[#525866] hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition-colors cursor-pointer"
                            title="Delete formulation record"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          ) : (
            /* Side-by-Side Comparison View */
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
                <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                  Side-by-Side Formulation Delta Analysis
                </h3>
                <button
                  onClick={() => setViewMode('list')}
                  className="text-xs font-heading font-bold uppercase tracking-wider text-[#2563EB] hover:underline"
                >
                  ← Back to Records
                </button>
              </div>

              {recordA && recordB && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border border-[#E5E5E0] rounded-xl overflow-hidden">
                    <thead className="bg-[#333A42] text-white text-left font-heading">
                      <tr>
                        <th className="p-3 border-r border-[#282E34] w-1/3">Parameter / Output</th>
                        <th className="p-3 border-r border-[#282E34] w-1/3">
                          <div>
                            <span className="font-bold">{recordA.name}</span>
                            <span className="block text-[10px] font-mono text-[#E5E5E0]">{recordA.id}</span>
                          </div>
                        </th>
                        <th className="p-3 w-1/3">
                          <div>
                            <span className="font-bold">{recordB.name}</span>
                            <span className="block text-[10px] font-mono text-[#E5E5E0]">{recordB.id}</span>
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5E5E0] font-mono text-[#1E2022]">
                      <tr className="bg-[#F5F5F3] font-sans font-bold">
                        <td colSpan={3} className="px-3 py-2 text-[11px] text-[#525866] uppercase">
                          Physical Mix Proportions
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Polymer Aggregate</td>
                        <td className="p-3 text-[#2563EB] font-bold">{recordA.mix_params?.plastic_type}</td>
                        <td className="p-3 text-[#2563EB] font-bold">{recordB.mix_params?.plastic_type}</td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Replacement (%)</td>
                        <td className="p-3">{recordA.mix_params?.replacement_pct}%</td>
                        <td className="p-3">{recordB.mix_params?.replacement_pct}%</td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Water / Cement (w/c)</td>
                        <td className="p-3">{recordA.mix_params?.wc_ratio}</td>
                        <td className="p-3">{recordB.mix_params?.wc_ratio}</td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Particle Size (mm)</td>
                        <td className="p-3">{recordA.mix_params?.particle_size_mm} mm</td>
                        <td className="p-3">{recordB.mix_params?.particle_size_mm} mm</td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">SCM Mineral Additive</td>
                        <td className="p-3">{recordA.mix_params?.additive_type} ({recordA.mix_params?.additive_pct}%)</td>
                        <td className="p-3">{recordB.mix_params?.additive_type} ({recordB.mix_params?.additive_pct}%)</td>
                      </tr>

                      <tr className="bg-[#F5F5F3] font-sans font-bold">
                        <td colSpan={3} className="px-3 py-2 text-[11px] text-[#525866] uppercase">
                          Predicted Properties & Sustainability
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Compressive Strength (MPa)</td>
                        <td className="p-3 font-bold text-base text-[#1E2022]">
                          {recordA.prediction?.predictions?.compressive_strength_mpa?.mean?.toFixed(2) ?? '—'} MPa
                        </td>
                        <td className="p-3 font-bold text-base text-[#1E2022]">
                          {recordB.prediction?.predictions?.compressive_strength_mpa?.mean?.toFixed(2) ?? '—'} MPa
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Embodied Carbon Saved</td>
                        <td className="p-3 text-emerald-700 font-bold">
                          {recordA.score?.co2_saving_pct != null ? `${recordA.score.co2_saving_pct.toFixed(1)}%` : '—'}
                        </td>
                        <td className="p-3 text-emerald-700 font-bold">
                          {recordB.score?.co2_saving_pct != null ? `${recordB.score.co2_saving_pct.toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Sustainability Grade</td>
                        <td className="p-3 font-bold">{recordA.score?.sustainability_grade ?? '—'}</td>
                        <td className="p-3 font-bold">{recordB.score?.sustainability_grade ?? '—'}</td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-semibold">Restore Formulation</td>
                        <td className="p-3">
                          <button
                            onClick={() => restoreSavedFormulation(recordA)}
                            className="px-3 py-1 rounded bg-[#2563EB] text-white text-xs font-semibold cursor-pointer"
                          >
                            Restore {recordA.id}
                          </button>
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => restoreSavedFormulation(recordB)}
                            className="px-3 py-1 rounded bg-[#2563EB] text-white text-xs font-semibold cursor-pointer"
                          >
                            Restore {recordB.id}
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
