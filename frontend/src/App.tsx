
import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Schema } from './pages/Schema';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useEffect, useState } from 'react';
import { checkHealth } from './services/api';

function App() {
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const initializeApp = async () => {
      try {
        await checkHealth();
      } catch (err) {
        console.warn("Backend not yet ready or failed health check", err);
      } finally {
        if (isMounted) {
          // Small simulated delay for premium smooth transition
          setTimeout(() => setIsInitializing(false), 800);
        }
      }
    };
    initializeApp();
    return () => { isMounted = false; };
  }, []);

  if (isInitializing) {
    return (
      <div className="fixed inset-0 bg-zinc-50 flex items-center justify-center z-50">
        <div className="flex flex-col items-center animate-fade-in">
          <div className="w-12 h-12 border-[3px] border-zinc-200 border-t-indigo-600 rounded-full animate-spin mb-6"></div>
          <h1 className="text-xl font-semibold text-zinc-800 tracking-tight mb-2">KnowUrDB</h1>
          <p className="text-sm text-zinc-500 font-medium">Connecting to intelligent backend...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="animate-fade-in">
        <AppShell>
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/history" element={<History />} />
            <Route path="/schema" element={<Schema />} />
          </Routes>
        </AppShell>
      </div>
    </ErrorBoundary>
  );
}

export default App;

