import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Schema } from './pages/Schema';
import { SourceLibrary } from './pages/SourceLibrary';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { CustomCursor } from './components/common/CustomCursor';
import { CinematicIntro } from './components/cinematic/CinematicIntro';
import { useEffect, useState, useCallback } from 'react';
import { checkHealth } from './services/api';

// Module level guard to ensure it only runs once per JS execution context (page load/refresh).
let hasRunLoadingExperience = false;

function App() {
  const [appStatus, setAppStatus] = useState<'loading' | 'revealing' | 'ready'>(
    hasRunLoadingExperience ? 'ready' : 'loading'
  );

  useEffect(() => {
    (window as any).__appReady = hasRunLoadingExperience;
    checkHealth().catch(err => {
      console.warn("Backend not yet ready or failed health check", err);
    });
  }, []);

  // Memoize callbacks to prevent new function references from triggering effects in child components
  const handleReveal = useCallback(() => {
    setAppStatus('revealing');
  }, []);

  const handleComplete = useCallback(() => {
    hasRunLoadingExperience = true;
    (window as any).__appReady = true;
    window.dispatchEvent(new Event('appReady'));
    setAppStatus('ready');
  }, []);

  return (
    <ErrorBoundary>
      <CustomCursor />
      
      {appStatus !== 'ready' && (
        <CinematicIntro 
          onReveal={handleReveal}
          onComplete={handleComplete} 
        />
      )}

      {/* Main App Layer */}
      <div 
        className={`transition-all duration-700 ease-out min-h-screen bg-[#09090b] text-zinc-100 selection:bg-cyan-500/30 selection:text-cyan-100 ${appStatus !== 'loading' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 pointer-events-none'}`}
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
