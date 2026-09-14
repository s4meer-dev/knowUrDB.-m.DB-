import React, { useEffect, useState } from 'react';
import { checkHealth, checkAiStatus } from '../../services/api';
import type { HealthResponse, AiStatusResponse } from '../../types';
import WarpText from '../WarpText/WarpText';

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
    <header className="bg-[#09090b]/80 backdrop-blur-xl border-b border-zinc-800/50 px-6 py-4 flex items-center justify-between sticky top-0 z-20 w-full transition-all">
        <div className="flex items-center space-x-3">
          <div className="relative w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.1)]">
            <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
            </svg>
          </div>
          <h1 className="text-xl font-bold text-zinc-100 tracking-tight flex items-center" aria-label="KnowUrDB">
            <WarpText
              text="KnowUrDB"
              color="#f4f4f5"
              warpStrength={0.18}
              warpScale={1.9}
              speed={0}
              pointerInfluence={0.31}
              pointerStrength={0.8}
              refraction={0.05}
              ripple={true}
              fontSize={20}
              fontWeight={700}
              letterSpacing="-0.025em"
              className="!min-h-0 h-[32px] w-[120px]"
              style={{ minHeight: '0' }}
              lineHeight={1.4}
            />
          </h1>
        </div>
      
      <div className="flex items-center space-x-4 text-xs font-semibold bg-zinc-900/50 px-4 py-2 rounded-xl border border-zinc-800 shadow-sm backdrop-blur-md">
        <div className="flex items-center space-x-2 border-r border-zinc-700/50 pr-4">
          <span className="text-zinc-500 tracking-wider">API</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 animate-pulse"></span>
            </span>
          ) : health ? (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
              Online
            </span>
          ) : (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></span>
              Offline
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-zinc-500 tracking-wider">AI</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-600 animate-pulse"></span>
            </span>
          ) : aiStatus?.status === 'ready' ? (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.5)]"></span>
              Ready
            </span>
          ) : aiStatus?.configured === false ? (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></span>
              Setup
            </span>
          ) : (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></span>
              Down
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
