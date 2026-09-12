import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Schema } from './pages/Schema';
import { SourceLibrary } from './pages/SourceLibrary';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { CustomCursor } from './components/common/CustomCursor';
import { LoadingExperience } from './components/LoadingExperience';
import { useEffect, useState } from 'react';
import { checkHealth } from './services/api';

function App() {
  const [showLoading, setShowLoading] = useState(true);
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    // Fire off the health check in the background.
    // The LoadingExperience component manages its own visual lifecycle.
    checkHealth().catch(err => {
      console.warn("Backend not yet ready or failed health check", err);
    });
  }, []);

  return (
    <ErrorBoundary>
      <CustomCursor />
      
      {showLoading && (
        <LoadingExperience 
          onReveal={() => setAppReady(true)}
          onComplete={() => setShowLoading(false)} 
        />
      )}

      {/* Main App Layer */}
      <div 
        className={`transition-all duration-700 ease-out min-h-screen bg-[#09090b] text-zinc-100 selection:bg-cyan-500/30 selection:text-cyan-100 ${appReady ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}
      >
        <AppShell>
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/sources" element={<SourceLibrary />} />
            <Route path="/history" element={<History />} />
            <Route path="/schema" element={<Schema />} />
          </Routes>
        </AppShell>
      </div>
    </ErrorBoundary>
  );
}

export default App;
