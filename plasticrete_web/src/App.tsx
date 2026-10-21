import React from 'react';
import { MixProvider, useMix } from './context/MixContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { Studio } from './pages/Studio';
import { StandardsPage } from './pages/StandardsPage';
import { TechPage } from './pages/TechPage';

const AppContent: React.FC = () => {
  const { mainRoute } = useMix();

  const renderCurrentView = () => {
    switch (mainRoute) {
      case 'home':
        return <LandingPage />;
      case 'studio':
        return <Studio />;
      case 'standards':
        return <StandardsPage />;
      case 'technology':
        return <TechPage />;
      default:
        return <LandingPage />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 transition-colors selection:bg-emerald-500 selection:text-white">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
