
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
      <div className="fixed inset-0 bg-[#09090b] flex flex-col items-center justify-center z-50 transition-opacity duration-700">
        <div className="flex flex-col items-center animate-fade-in relative">
          <div className="absolute inset-0 bg-cyan-500/10 blur-3xl rounded-full scale-150"></div>
          
          <div className="relative w-16 h-16 flex items-center justify-center mb-8">
            <div className="absolute inset-0 border border-zinc-800 rounded-full"></div>
            <div className="absolute inset-0 border border-cyan-500 rounded-full animate-[spin_3s_linear_infinite] border-t-transparent border-l-transparent"></div>
            <div className="absolute inset-2 border border-zinc-700 rounded-full animate-[spin_4s_linear_infinite_reverse] border-r-transparent border-b-transparent"></div>
            <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-white tracking-tight mb-3">KnowUrDB</h1>
          <div className="flex flex-col items-center gap-1.5">
            <p className="text-sm text-zinc-400 font-medium tracking-wide uppercase text-[11px]">Understanding your data</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></span>
              <span className="text-xs text-zinc-500 font-mono">INITIALIZING SYSTEM...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="animate-fade-in min-h-screen bg-[#09090b] text-zinc-100 selection:bg-cyan-500/30 selection:text-cyan-100">
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

