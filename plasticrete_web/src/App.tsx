import React, { useEffect } from 'react';
import { MixProvider, useMix } from './context/MixContext';
import { revealTarget, takeQueuedAnchor } from './routing';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { Studio } from './pages/Studio';
import { StandardsPage } from './pages/StandardsPage';
import { InteractivePage } from './pages/InteractivePage';
import { BatchPassportPage } from './pages/BatchPassportPage';
import { AlertTriangle, RefreshCw } from 'lucide-react';

const AppContent: React.FC = () => {
  const { mainRoute, studioTab, batchId, serviceError, refreshAll } = useMix();

  useEffect(() => {
    const anchor = takeQueuedAnchor();
    const frame = requestAnimationFrame(() => revealTarget(anchor));
    return () => cancelAnimationFrame(frame);
  }, [mainRoute, studioTab, batchId]);

  const renderCurrentView = () => {
    switch (mainRoute) {
      case 'home':
        return <LandingPage />;
      case 'studio':
        return <Studio />;
      case 'interactive':
        return <InteractivePage />;
      case 'standards':
        return <StandardsPage />;
      case 'batch':
        return <BatchPassportPage batchId={batchId} />;
      default:
        return <LandingPage />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F5F3] text-[#1E2022] font-sans antialiased">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {serviceError && (
          <div className="mb-6 rounded-lg border border-[#F97316]/40 bg-[#FFF7ED] p-4 text-xs text-[#1E2022] flex items-start justify-between gap-3 shadow-xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-[#1E2022] block font-heading uppercase tracking-wider text-[11px]">
                  The prediction service is temporarily unavailable
                </span>
                <p className="mt-0.5 text-[#525866] leading-relaxed">
                  Your saved mix is unchanged. Try again or review the inputs. {serviceError}
                </p>
              </div>
            </div>
            <button
              onClick={() => refreshAll()}
              className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E5E5E0] bg-white text-xs font-semibold text-[#1E2022] hover:bg-[#F5F5F3] transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>Retry</span>
            </button>
          </div>
        )}
        {renderCurrentView()}
      </main>
      <Footer />
    </div>
  );
};

export function App() {
  return (
    <MixProvider>
      <AppContent />
    </MixProvider>
  );
}

export default App;
