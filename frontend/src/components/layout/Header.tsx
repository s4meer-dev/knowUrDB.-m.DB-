import React, { useEffect, useState } from 'react';
import { checkHealth, checkAiStatus } from '../../services/api';
import type { HealthResponse, AiStatusResponse } from '../../types';

export const Header: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatusResponse | null>(null);
  const [backendLoading, setBackendLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    
    const fetchStatus = async () => {
      try {
        setBackendLoading(true);
        const [healthData, aiData] = await Promise.all([
          checkHealth().catch(() => null),
          checkAiStatus().catch(() => null)
        ]);
        
        if (isMounted) {
          setHealth(healthData);
          setAiStatus(aiData);
        }
      } finally {
        if (isMounted) {
          setBackendLoading(false);
        }
      }
    };

    fetchStatus();
    
    // Poll every 30 seconds
    const interval = setInterval(fetchStatus, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-zinc-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10 w-full transition-all">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 rounded-lg bg-zinc-900 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
          </svg>
        </div>
        <h1 className="text-xl font-bold text-zinc-900 tracking-tight">KnowUrDB</h1>
      </div>
      
      <div className="flex items-center space-x-4 text-xs font-medium bg-zinc-100/50 px-3 py-1.5 rounded-full border border-zinc-200/60">
        <div className="flex items-center space-x-2 border-r border-zinc-200 pr-4">
          <span className="text-zinc-500">API</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"></span>
            </span>
          ) : health ? (
            <span className="flex items-center gap-1.5 text-zinc-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Online
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-zinc-700">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              Offline
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-zinc-500">AI</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"></span>
            </span>
          ) : aiStatus?.status === 'ready' ? (
            <span className="flex items-center gap-1.5 text-zinc-700">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
              Ready
            </span>
          ) : aiStatus?.configured === false ? (
            <span className="flex items-center gap-1.5 text-zinc-700">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Setup
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-zinc-700">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              Down
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
