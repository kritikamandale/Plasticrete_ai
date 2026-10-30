import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import { OperationProgress } from '../components/OperationProgress';
import { TechnicalDetails } from '../components/TechnicalDetails';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';

const FEATURE_PRETTY_NAMES: Record<string, string> = {
  replacement_pct_x_wc_ratio: 'Replacement × water/cement ratio',
  replacement_pct: 'Plastic replacement',
  plastic_type: 'Polymer type',
  wc_ratio: 'Water/cement ratio',
  particle_size_mm: 'Particle size',
  log_particle_size_mm: 'Log particle size',
  curing_temp_c: 'Curing temperature',
  curing_days: 'Curing age',
  log_curing_days: 'Log curing age',
  additive_type: 'Mineral additive',
  additive_pct: 'Additive dosage',
  replacement_pct_x_additive_pct: 'Replacement × additive dosage',
  is_plain_concrete: 'Plain concrete (no plastic)',
};

export const Explainability: React.FC = () => {
  const {
    prediction,
    loading,
    refreshAll,
    operationStatus,
    operationStartTime,
    cancelOperation,
  } = useMix();

  const [selectedTarget, setSelectedTarget] = useState<'compressive_strength_mpa' | 'durability_index'>(
    'compressive_strength_mpa'
  );

  const shapDict = prediction?.shap_values?.[selectedTarget] || {};
  const finalPrediction = prediction?.predictions?.[selectedTarget]?.mean;
  const unit = selectedTarget === 'compressive_strength_mpa' ? 'MPa' : '/100';
  const propertyLabel = selectedTarget === 'compressive_strength_mpa' ? 'compressive strength' : 'durability index';

  const chartData = Object.entries(shapDict).map(([feature, impact]) => {
    const num = typeof impact === 'number' ? impact : parseFloat(String(impact));
    return {
      rawFeature: feature,
      feature: FEATURE_PRETTY_NAMES[feature] || feature.replace(/_/g, ' '),
      impact: Number(num.toFixed(3)),
    };
  }).sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  const hasShapData = chartData.length > 0;
  const raisers = chartData.filter((row) => row.impact > 0);
  const lowerers = chartData.filter((row) => row.impact < 0);
  const topRaiser = raisers[0];
  const topLowerer = lowerers[0];
  const explanationFailed = !loading && !hasShapData && (operationStatus === 'error' || operationStatus === 'timeout');
  const explanationPending = loading && !hasShapData;
  const explanationUnavailable = !loading && !hasShapData && !explanationFailed;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-heading font-bold text-[#1E2022] tracking-tight">
            Why this mix is predicted to perform this way
          </h2>
          <p className="text-xs text-[#525866] mt-1 max-w-2xl leading-relaxed">
            These bars show how each mix input moved this particular {propertyLabel} prediction. They explain the model, not a laboratory cube, and they do not prove physical causation.
          </p>
        </div>
        <div className="flex rounded-lg bg-[#F5F5F3] p-1 border border-[#E5E5E0] text-xs font-semibold">
          <button
            onClick={() => setSelectedTarget('compressive_strength_mpa')}
            className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
              selectedTarget === 'compressive_strength_mpa'
                ? 'bg-[#333A42] text-white shadow-xs'
                : 'text-[#525866] hover:text-[#1E2022]'
            }`}
          >
            Compressive strength (MPa)
          </button>
          <button
            onClick={() => setSelectedTarget('durability_index')}
            className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
              selectedTarget === 'durability_index'
                ? 'bg-[#333A42] text-white shadow-xs'
                : 'text-[#525866] hover:text-[#1E2022]'
            }`}
          >
            Durability index (/100)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="engineering-card rounded-xl p-4 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <span className="eyebrow-tag text-[10px] text-[#525866] block mb-1">Predicted {propertyLabel}</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#1E2022]">
              {finalPrediction != null ? finalPrediction.toFixed(2) : '—'}
            </span>
            <span className="text-xs font-mono text-[#525866]">{unit}</span>
          </div>
          <p className="text-[11px] text-[#525866] mt-1">
            Model estimate for this mix. This is not a measured cube result.
          </p>
        </div>
        <div className="engineering-card rounded-xl p-4 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
          <span className="eyebrow-tag text-[10px] text-[#525866] block mb-1">How to read the bars</span>
          <p className="text-xs text-[#525866] leading-relaxed mt-1">
            Blue bars pushed the prediction up. Orange bars pulled it down. The service does not return a separate reference prediction to add to the bars, so the bars explain direction of influence, not a reconstructed total.
          </p>
        </div>
      </div>

      {hasShapData && (
        <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-2 text-xs text-[#525866]">
          {topRaiser && (
            <p>
              <strong className="text-[#1E2022]">{topRaiser.feature}</strong> had the largest upward effect ({topRaiser.impact > 0 ? '+' : ''}{topRaiser.impact.toFixed(3)} {unit}).
            </p>
          )}
          {topLowerer && (
            <p>
              <strong className="text-[#1E2022]">{topLowerer.feature}</strong> had the largest downward effect ({topLowerer.impact.toFixed(3)} {unit}).
            </p>
          )}
          <p>A large effect here means the model used that input strongly for this mix. It does not by itself prove a physical cause on site.</p>
        </div>
      )}

      <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0] mb-4">
          <div>
            <h3 className="font-heading font-bold text-[#1E2022] text-sm">
              Factors affecting this prediction
            </h3>
            <p className="text-xs text-[#525866]">
              Shown only when the explainer returned values. Units match the selected property.
            </p>
          </div>
          {hasShapData && (
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
                <span className="text-[#525866]">Raised prediction</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F97316]" />
                <span className="text-[#525866]">Lowered prediction</span>
              </span>
            </div>
          )}
        </div>

        {explanationPending || explanationFailed || explanationUnavailable ? (
          <div className="py-4">
            <OperationProgress
              title={
                explanationPending
                  ? 'Preparing the explanation…'
                  : explanationFailed
                  ? 'The explanation could not be generated'
                  : 'Explanation not returned'
              }
              description={
                explanationPending
                  ? 'The prediction may already be available. The explanation is a separate result from the same request.'
                  : 'The explanation could not be generated. Your prediction is still available if it was returned.'
              }
              status={
                explanationPending
                  ? (operationStatus === 'idle' ? 'running' : operationStatus)
                  : explanationFailed
                  ? operationStatus
                  : 'error'
              }
              startTime={operationStartTime}
              expectedDurationMs={3500}
              onRetry={() => refreshAll()}
              onCancel={loading ? cancelOperation : undefined}
            />
          </div>
        ) : (
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 160, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="#525866"
                  fontSize={11}
                  tickLine={false}
                  unit={selectedTarget === 'compressive_strength_mpa' ? ' MPa' : ''}
                />
                <YAxis
                  type="category"
                  dataKey="feature"
                  stroke="#525866"
                  fontSize={11}
                  tickLine={false}
                  width={155}
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
                  formatter={(val: unknown) => [
                    `${typeof val === 'number' ? (val > 0 ? `+${val.toFixed(3)}` : val.toFixed(3)) : val} ${unit}`,
                    'Effect on this prediction',
                  ]}
                />
                <ReferenceLine x={0} stroke="#333A42" strokeWidth={1.5} />
                <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.impact >= 0 ? '#2563EB' : '#F97316'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <TechnicalDetails title="Technical details (SHAP)">
        <p>
          The explainer is SHAP (SHapley Additive exPlanations / TreeSHAP) on the existing property model. Values are local attributions for the current mix.
        </p>
        <p>
          A reference (base) prediction is not returned by this service, so bars must not be added up to reconstruct the predicted mean. Contribution is not physical causation.
        </p>
        <p>
          If this panel is empty, the prediction request did not include SHAP values. A failed explanation does not erase a successful property prediction.
        </p>
      </TechnicalDetails>
    </div>
  );
};
