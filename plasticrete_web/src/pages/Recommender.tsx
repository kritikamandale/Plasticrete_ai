import React from 'react';
import { useMix } from '../context/MixContext';
import { APPLICATION_PRETTY_NAMES } from '../types';
import { ExternalLink, BookOpen } from 'lucide-react';
import { TechnicalDetails } from '../components/TechnicalDetails';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';

export const Recommender: React.FC = () => {
  const { recommendation, activeMix } = useMix();

  const cb = recommendation?.cost_benefit;
  const analogues = recommendation?.rag_analogues || [];

  // Suitability scores formatted for horizontal bar chart
  const suitabilityData = recommendation?.suitability_scores
    ? Object.entries(recommendation.suitability_scores)
        .map(([appKey, matchScore]) => ({
          name: APPLICATION_PRETTY_NAMES[appKey] || appKey,
          score: Number(matchScore.toFixed(1)),
          isPrimary: appKey === recommendation.primary_application,
        }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 6)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div>
            <h2 className="text-xl font-heading font-bold text-[#1E2022] tracking-tight">
              Explore applications
            </h2>
            <p className="text-xs text-[#525866] mt-1 max-w-2xl leading-relaxed">
              Suggested construction uses for this mix, with supporting technical references when the retrieval service returns them.
            </p>
          </div>
        </div>
      </div>

      {/* Top Section: Suitability Ranking Chart (Left) and Techno-Economic Card (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Suitability Ranking Horizontal Bar Chart (7 cols) */}
        <div className="lg:col-span-7 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <div>
                <h3 className="font-heading font-bold text-sm text-[#1E2022]">
                  Suggested uses
                </h3>
                <p className="text-xs text-[#525866]">
                  How closely this mix matches each use class, as returned by the application service.
                </p>
              </div>
              <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
                {recommendation?.primary_confidence_pct != null
                  ? `Top match ${recommendation.primary_confidence_pct}%`
                  : 'Match not returned'}
              </span>
            </div>

            <div className="h-64 w-full pt-1">
              {suitabilityData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={suitabilityData}
                    layout="vertical"
                    margin={{ top: 10, right: 30, left: 140, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#525866"
                      fontSize={11}
                      tickLine={false}
                      unit="%"
                      domain={[0, 100]}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      stroke="#525866"
                      fontSize={11}
                      tickLine={false}
                      width={135}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#333A42',
                        borderColor: '#282E34',
                        borderRadius: '8px',
                        color: '#FFFFFF',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                      }}
                      formatter={(val) => [`${val}%`, 'Suitability Match']}
                    />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                      {suitabilityData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.isPrimary ? '#2563EB' : '#333A42'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs font-mono text-[#525866]">
                  Suggested uses appear after the application service returns scores.
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] mt-2 flex items-center justify-between text-xs font-mono">
            <span className="text-[#525866]">Screening of the top use:</span>
            <span className="font-bold text-[#2563EB]">
              {recommendation?.primary_gate_status === 'allowed' ? 'Meets selected screening criterion' :
               recommendation?.primary_gate_status === 'verification_batch' ? 'Verification batch needed' :
               recommendation?.primary_gate_status === 'lab_trial' ? 'Laboratory trial only' :
               recommendation?.primary_gate_status === 'refused' ? 'Does not meet the selected criterion' :
               'Screening not returned'}
            </span>
          </div>
        </div>

        {/* Commercial Techno-Economic Assessment (5 cols) */}
        <div className="lg:col-span-5 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-3">
              <span className="eyebrow-tag text-[10px] text-[#525866]">Estimated material cost</span>
              <span className="font-mono text-xs font-bold text-[#2563EB]">
                {cb?.cost_saving_pct != null ? `${cb.cost_saving_pct > 0 ? '+' : ''}${cb.cost_saving_pct.toFixed(1)}% vs conventional` : 'Cost not returned'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="p-3 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-mono text-[#525866] block">Composite Mix Cost</span>
                <span className="text-lg font-bold font-mono text-[#1E2022]">
                  ₹{cb?.plastic_mix_cost_inr_m3?.toFixed(0) ?? '—'}
                </span>
                <span className="text-[10px] font-mono text-[#525866] block">/ m³ batch</span>
              </div>

              <div className="p-3 rounded-lg border border-[#E5E5E0] bg-[#F5F5F3]">
                <span className="text-[10px] font-mono text-[#525866] block">Conventional Cost</span>
                <span className="text-lg font-bold font-mono text-[#525866]">
                  ₹{cb?.conventional_cost_inr_m3?.toFixed(0) ?? '—'}
                </span>
                <span className="text-[10px] font-mono text-[#525866] block">/ m³ baseline</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-mono text-emerald-800 space-y-1">
              <div className="flex justify-between font-bold">
                <span>Net Cost Saving:</span>
                <span>₹{cb?.cost_saving_inr_m3 != null ? Math.abs(cb.cost_saving_inr_m3).toFixed(0) : '—'} / m³</span>
              </div>
              <p className="text-[11px] font-sans text-emerald-700">
                {cb?.product_yield_m2_per_m3 != null
                  ? `Unit product yield: ${cb.product_yield_m2_per_m3} m² per cubic metre.`
                  : 'Product yield was not returned for this mix.'}
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-[#E5E5E0] text-[11px] text-[#525866]">
            Cost uses the configured Indian material rates in this project. Missing fields stay blank.
          </div>
        </div>
      </div>

      {/* FAISS Semantic Literature Analogues Section */}
      <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[#2563EB]" />
            <div>
              <h3 className="font-heading font-bold text-[#1E2022] text-sm">
                Technical references
              </h3>
              <p className="text-xs text-[#525866]">
                Supporting papers returned for mixes using {activeMix.plastic_type}. Only items the retrieval service actually returned are listed.
              </p>
            </div>
          </div>
          <span className="eyebrow-tag text-[9px] text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
            {analogues.length} returned
          </span>
        </div>

        {analogues.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {analogues.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-[#E5E5E0] bg-[#FFFFFF] hover:border-[#333A42]/30 transition-all flex flex-col justify-between space-y-3 shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[#525866] mb-1">
                    <span className="font-bold text-[#2563EB]">Rank #{item.rank || idx + 1}</span>
                    <span>{item.verified ? 'Returned as verified' : 'As returned'}</span>
                  </div>
                  <h4 className="font-heading font-bold text-xs text-[#1E2022] line-clamp-2">
                    {item.author}{item.year ? ` (${item.year})` : ''}
                  </h4>
                  <p className="text-[11px] text-[#525866] mt-1 line-clamp-1 italic">
                    {item.journal || 'Journal not returned'}
                  </p>
                  <div className="mt-2 text-[10px] font-mono text-[#333A42] bg-[#F5F5F3] p-1.5 rounded border border-[#E5E5E0]">
                    Tested Application: {item.primary_application}
                  </div>
                </div>

                <div className="pt-2 border-t border-[#E5E5E0] flex items-center justify-between text-[11px]">
                  <span className="font-mono text-[10px] text-[#525866]">
                    {item.year ? `Year ${item.year}` : 'Year not returned'}
                  </span>
                  {item.doi && (
                    <a
                      href={`https://doi.org/${item.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[#2563EB] hover:underline font-mono text-[10px] font-bold"
                    >
                      <span>DOI Link</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs font-mono text-[#525866]">
            No technical references were returned for this mix.
          </div>
        )}
      </div>

      <TechnicalDetails>
        <p>Suggested uses come from the existing multi-label application classifier. Technical references come from the existing retrieval index (FAISS). Retrieval distance is not shown in the main list because it is not a construction quantity.</p>
        <p>
          {analogues.length > 0
            ? `Returned retrieval distances: ${analogues.map((item) => (item.l2_distance != null ? item.l2_distance.toFixed(2) : 'not returned')).join(', ')}.`
            : 'No retrieval distances were returned.'}
        </p>
      </TechnicalDetails>
    </div>
  );
};
