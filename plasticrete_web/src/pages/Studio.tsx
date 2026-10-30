import React, { useState } from 'react';
import { useMix } from '../context/MixContext';
import { generateReport, createBatch } from '../api/client';
import { Dashboard } from './Dashboard';
import { Predictor } from './Predictor';
import { Optimizer } from './Optimizer';
import { Sustainability } from './Sustainability';
import { Recommender } from './Recommender';
import { Explainability } from './Explainability';
import { PipelineNav } from '../components/PipelineNav';
import { MixEditDrawer } from '../components/MixEditDrawer';
import { FormulationHistoryModal } from '../components/FormulationHistoryModal';
import {
  Home,
  ChevronRight,
  FileDown,
  Loader2,
  CheckCircle2,
  FlaskConical,
} from 'lucide-react';

type ReportStatus = 'idle' | 'loading' | 'success' | 'api_unavailable';

export const Studio: React.FC = () => {
  const {
    studioTab,
    setMainRoute,
    mix,
    prediction,
    score,
    recommendation,
    openBatch,
    batchId,
    loading,
  } = useMix();
  const [reportStatus, setReportStatus] = useState<ReportStatus>('idle');
  const [batchMessage, setBatchMessage] = useState<string>('');

  const handleDownloadReport = async () => {
    if (!prediction || !score || !recommendation) {
      setReportStatus('api_unavailable');
      setTimeout(() => setReportStatus('idle'), 5000);
      return;
    }
    setReportStatus('loading');
    const sessionId = `PLT-${Date.now().toString(36).toUpperCase()}`;
    try {
      await generateReport(mix, prediction, score, recommendation, sessionId, batchId ?? undefined);
      setReportStatus('success');
      setTimeout(() => setReportStatus('idle'), 3000);
    } catch (err) {
      setBatchMessage(err instanceof Error ? err.message : 'PDF generation failed.');
      setReportStatus('api_unavailable');
      setTimeout(() => setReportStatus('idle'), 5000);
    }
  };

  const handleCreateBatch = async () => {
    if (!prediction || !score || !recommendation) {
      setBatchMessage('Cannot save batch: awaiting complete model predictions.');
      return;
    }
    setBatchMessage('');
    try {
      const res = await createBatch({
        plant_name: 'PlastiCrete Pilot Plant #1',
        cast_date: new Date().toISOString().slice(0, 10),
        mix_params: mix,
        prediction,
        score,
        recommendation,
      });
      openBatch(res.id);
      setBatchMessage(`Batch ${res.id} created and registered.`);
    } catch (err) {
      setBatchMessage(err instanceof Error ? err.message : 'Batch creation failed.');
    }
  };

  const renderContent = () => {
    switch (studioTab) {
      case 'overview':
        return <Dashboard />;
      case 'predictor':
        return <Predictor />;
      case 'optimizer':
        return <Optimizer />;
      case 'sustainability':
        return <Sustainability />;
      case 'recommender':
        return <Recommender />;
      case 'explainability':
        return <Explainability />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Studio Top Control Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E0]">
        <div>
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs font-semibold text-[#525866] mb-1">
            <button
              onClick={() => setMainRoute('home')}
              className="flex items-center gap-1 hover:text-[#1E2022] transition-colors cursor-pointer"
            >
              <Home className="w-3.5 h-3.5" />
              <span>Home</span>
            </button>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-[#1E2022] font-bold">Mix workspace</span>
          </div>
          <h1 className="text-2xl font-heading font-bold text-[#1E2022] tracking-tight">
            Mix workspace
          </h1>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleCreateBatch}
            disabled={loading || !prediction || !score || !recommendation}
            title={loading ? 'Wait until the prediction is ready' : 'Cast this mix and record the laboratory cube'}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#333A42] hover:bg-[#282E34] text-white text-xs font-semibold transition-all cursor-pointer shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FlaskConical className="w-4 h-4 text-[#2563EB]" />
            <span>Cast & Record Batch</span>
          </button>

          <button
            onClick={handleDownloadReport}
            disabled={reportStatus === 'loading'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-all cursor-pointer shadow-xs disabled:opacity-50"
          >
            {reportStatus === 'loading' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : reportStatus === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-white" />
            ) : (
              <FileDown className="w-4 h-4" />
            )}
            <span>{reportStatus === 'loading' ? 'Preparing mix report…' : 'Download mix report'}</span>
          </button>
        </div>
      </div>

      {/* Batch Message Notification */}
      {batchMessage && (
        <div className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] text-xs text-[#1E2022] flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-[#2563EB]" />
            <span className="font-medium">{batchMessage}</span>
          </div>
          <button onClick={() => setBatchMessage('')} className="p-1 text-[#525866] hover:text-[#1E2022] rounded cursor-pointer">✕</button>
        </div>
      )}

      {/* Connected M1 -> M4 Pipeline Navigation Bar */}
      <PipelineNav />

      {/* Active Sub-tab View */}
      <div className="pt-2">
        {renderContent()}
      </div>

      {/* Slide-over Mix Edit Drawer and History Modal */}
      <MixEditDrawer />
      <FormulationHistoryModal />
    </div>
  );
};
