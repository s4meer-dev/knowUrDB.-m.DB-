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
    <header className="bg-[#09090b]/80 backdrop-blur-xl border-b border-zinc-800/50 px-6 py-5 flex items-center justify-between sticky top-0 z-20 w-full transition-all">
        <div className="brand-area flex items-center cursor-default">
          <h1 className="text-2xl font-bold text-zinc-100 tracking-tight flex items-center" aria-label="KnowUrDB">
            <WarpText
              mode="knowurdb-logo"
              text="KnowUrDB"
              color="#f8f5ff"
              warpStrength={0.15}
              warpScale={2.1}
              speed={1.5}
              pointerInfluence={1.2}
              pointerStrength={1.8}
              refraction={0.05}
              ripple={true}
              fontSize={28}
              fontWeight={800}
              letterSpacing="-0.025em"
              className="!min-h-0 h-[80px] w-[260px] -my-5"
              style={{ minHeight: '0' }}
              lineHeight={1.4}
            />
          </h1>
        </div>
      
      <div className="group relative flex items-center space-x-5 text-sm font-semibold bg-zinc-900/60 px-6 py-2.5 rounded-2xl border border-zinc-800/80 shadow-[0_0_15px_rgba(0,0,0,0.5)] backdrop-blur-md cursor-default transition-all duration-500 hover:border-cyan-500/40 hover:bg-zinc-900/80 hover:shadow-[0_0_25px_rgba(34,211,238,0.15)] overflow-hidden">
        {/* Animated Background Gradient on Hover */}
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/5 to-purple-500/5 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out pointer-events-none"></div>
        
        {/* API Status */}
        <div className="flex items-center space-x-2.5 relative z-10">
          <span className="text-zinc-500 text-xs tracking-[0.2em] uppercase transition-colors duration-300 group-hover:text-zinc-400">API</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse"></span>
            </span>
          ) : health ? (
            <span className="flex items-center gap-2 text-zinc-300 transition-colors duration-300 group-hover:text-zinc-100">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
              </span>
              <span className="text-[13px]">Online</span>
            </span>
          ) : (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
              </span>
              <span className="text-[13px]">Offline</span>
            </span>
          )}
        </div>
        
        {/* Divider with glow */}
        <div className="w-[1px] h-6 bg-zinc-800/80 group-hover:bg-cyan-500/30 transition-colors duration-500 relative z-10 shadow-[0_0_10px_rgba(34,211,238,0)] group-hover:shadow-[0_0_10px_rgba(34,211,238,0.5)]"></div>
        
        {/* AI Status */}
        <div className="flex items-center space-x-2.5 relative z-10">
          <span className="text-zinc-500 text-xs tracking-[0.2em] uppercase transition-colors duration-300 group-hover:text-zinc-400">AI</span>
          {backendLoading ? (
            <span className="flex items-center">
              <span className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse"></span>
            </span>
          ) : aiStatus?.status === 'ready' ? (
            <span className="flex items-center gap-2 text-zinc-300 transition-colors duration-300 group-hover:text-zinc-100">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.8)]"></span>
              </span>
              <span className="text-[13px]">Ready</span>
            </span>
          ) : aiStatus?.configured === false ? (
            <span className="flex items-center gap-2 text-zinc-300 transition-colors duration-300 group-hover:text-zinc-100">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]"></span>
              </span>
              <span className="text-[13px]">Setup</span>
            </span>
          ) : (
            <span className="flex items-center gap-2 text-zinc-300">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
              </span>
              <span className="text-[13px]">Down</span>
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
