import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Schema } from './pages/Schema';
import { SourceLibrary } from './pages/SourceLibrary';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { CustomCursor } from './components/common/CustomCursor';
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
          // 2 second simulated delay for premium galaxy intro
          setTimeout(() => setIsInitializing(false), 2000);
        }
      }
    };
    initializeApp();
    return () => { isMounted = false; };
  }, []);

  return (
    <ErrorBoundary>
      <CustomCursor />
      
      {/* Galaxy Intro Layer */}
      <div 
        className={`fixed inset-0 z-50 pointer-events-none transition-opacity duration-1000 ease-in-out ${isInitializing ? 'opacity-100' : 'opacity-0'}`}
        style={{
          background: 'radial-gradient(ellipse at center, #1e1b4b 0%, #09090b 70%)'
        }}
      >
        <div className="absolute inset-0 overflow-hidden">
          {/* Subtle moving particles/stars */}
          <div className="absolute w-[200%] h-[200%] top-[-50%] left-[-50%] opacity-20 animate-[spin_60s_linear_infinite]" 
               style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '50px 50px' }}></div>
          <div className="absolute w-[200%] h-[200%] top-[-50%] left-[-50%] opacity-30 animate-[spin_40s_linear_infinite_reverse]" 
               style={{ backgroundImage: 'radial-gradient(circle, #22d3ee 1px, transparent 1px)', backgroundSize: '70px 70px' }}></div>
        </div>
        
        <div className="flex flex-col items-center justify-center h-full relative z-10 animate-fade-in">
          <div className="absolute inset-0 bg-cyan-500/5 blur-3xl rounded-full scale-150 animate-pulse-slow"></div>
          
          <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight mb-4 drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
            KnowUrDB
          </h1>
          <p className="text-sm md:text-base text-zinc-400 font-medium tracking-[0.2em] uppercase">
            Ask your database anything.
          </p>
        </div>
      </div>

      {/* Main App Layer */}
      <div className={`transition-opacity duration-700 ease-in-out min-h-screen bg-[#09090b] text-zinc-100 selection:bg-cyan-500/30 selection:text-cyan-100 ${isInitializing ? 'opacity-0' : 'opacity-100'}`}>
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
