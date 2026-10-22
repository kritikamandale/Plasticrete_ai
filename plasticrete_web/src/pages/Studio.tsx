import React, { useState } from 'react';
import { useMix, type StudioSubTab } from '../context/MixContext';
import { generateReport, createBatch } from '../api/client';
import { Dashboard } from './Dashboard';
import { Predictor } from './Predictor';
import { Optimizer } from './Optimizer';
import { Sustainability } from './Sustainability';
import { Recommender } from './Recommender';
import { Explainability } from './Explainability';
import {
  LayoutDashboard,
  SlidersHorizontal,
  Leaf,
  Boxes,
  HelpCircle,
  Home,
  ChevronRight,
  FileDown,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

interface TabItem {
  id: StudioSubTab;
  label: string;
  badge?: string;
  icon: React.ComponentType<{ className?: string }>;
}

const STUDIO_TABS: TabItem[] = [
  { id: 'overview',        label: 'Overview & Properties (M1)', icon: LayoutDashboard },
  { id: 'predictor',       label: 'Property Predictor (M1)',    icon: LayoutDashboard },
  { id: 'optimizer',       label: 'Mix Optimiser (M2)',          icon: SlidersHorizontal, badge: 'M1' },
  { id: 'sustainability',  label: 'Carbon LCA & Gate (M3)',      icon: Leaf },
  { id: 'recommender',     label: 'Product Finder (M4)',         icon: Boxes },
  { id: 'explainability',  label: 'SHAP Explainability',         icon: HelpCircle },
];

type ReportStatus = 'idle' | 'loading' | 'success' | 'api_unavailable';

export const Studio: React.FC = () => {
  const { studioTab, setStudioTab, setMainRoute, mix, prediction, score, recommendation, openBatch, batchId } = useMix();
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

  const renderContent = () => {
    switch (studioTab) {
      case 'overview':       return <Dashboard />;
      case 'predictor':      return <Predictor />;
      case 'optimizer':      return <Optimizer />;
      case 'sustainability': return <Sustainability />;
      case 'recommender':    return <Recommender />;
      case 'explainability': return <Explainability />;
      default:               return <Dashboard />;
    }
  };

  const reportBtnLabel: Record<ReportStatus, string> = {
    idle:            'Download PDF Report',
    loading:         'Generating Report…',
    success:         'Report Downloaded!',
    api_unavailable: 'Start API Server First',
  };

  const ReportIcon: Record<ReportStatus, React.ComponentType<{ className?: string }>> = {
    idle:            FileDown,
    loading:         Loader2,
    success:         CheckCircle2,
    api_unavailable: AlertCircle,
  };

  const reportBtnClass: Record<ReportStatus, string> = {
    idle:            'bg-emerald-700 hover:bg-emerald-600 text-white shadow-md hover:shadow-emerald-500/20',
    loading:         'bg-emerald-700/70 text-white cursor-not-allowed',
    success:         'bg-emerald-600 text-white',
    api_unavailable: 'bg-amber-600 text-white',
  };

  const Icon = ReportIcon[reportStatus];

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div className="flex items-center gap-2 text-xs text-slate-800 font-bold">
          <button
            onClick={() => setMainRoute('home')}
            className="flex items-center gap-1 hover:text-slate-950 transition-colors cursor-pointer"
          >
            <Home className="w-4 h-4 text-slate-700" />
            <span>Home</span>
          </button>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          <span className="text-slate-950 font-extrabold">AI Engineering Studio</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={async () => {
              if (!prediction || !score || !recommendation) {
                setBatchMessage('Run a mix first, then save the batch.');
                return;
              }
              try {
                const saved = await createBatch({
                  plant_name: 'Plant',
                  mix_params: mix,
                  prediction,
                  score,
                  recommendation,
                });
                setBatchMessage(`Saved ${saved.id}`);
                openBatch(saved.id);
              } catch (err) {
                setBatchMessage(err instanceof Error ? err.message : 'Could not save the batch.');
              }
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold tracking-wide bg-white text-slate-900 border border-slate-300 hover:bg-slate-100 cursor-pointer"
          >
            Save batch passport
          </button>
          <button
            id="download-report-btn"
            onClick={handleDownloadReport}
            disabled={reportStatus === 'loading'}
            title="Generate a PDF with the shared mass balance, use-class gate, and a QR code when a batch is saved"
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold tracking-wide transition-all cursor-pointer ${reportBtnClass[reportStatus]}`}
          >
            <Icon className={`w-4 h-4 ${reportStatus === 'loading' ? 'animate-spin' : ''}`} />
            <span>{reportBtnLabel[reportStatus]}</span>
          </button>
        </div>
      </div>

      {batchMessage && (
        <p className="text-xs font-semibold text-slate-700">{batchMessage}</p>
      )}
      {reportStatus === 'api_unavailable' && (
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            <b>PDF Report requires the FastAPI backend.</b> Start it with:{' '}
            <code className="font-mono bg-amber-100 px-1.5 py-0.5 rounded text-amber-900">
              uvicorn deployment.api.app:app --reload
            </code>{' '}
            from the <code className="font-mono bg-amber-100 px-1 rounded">plasticrete_ai/</code> directory.
            Once running, the report will be generated and downloaded automatically.
          </span>
        </div>
      )}

      {/* Horizontal Studio Sub-Tabs Bar */}
      <div className="glass-card rounded-2xl p-2 flex flex-wrap items-center gap-1.5 border border-slate-300/80 shadow-md">
        {STUDIO_TABS.map((tab) => {
          const TabIcon = tab.icon;
          const isActive = studioTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`studio-tab-${tab.id}`}
              onClick={() => setStudioTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                isActive
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'text-slate-800 hover:text-slate-950 hover:bg-slate-200/80'
              }`}
            >
              <TabIcon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-700'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                  isActive ? 'bg-white/20 text-emerald-300' : 'bg-slate-200 text-slate-900'
                }`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active Tab Content */}
      <div className="pt-2">
        {renderContent()}
      </div>
    </div>
  );
};
