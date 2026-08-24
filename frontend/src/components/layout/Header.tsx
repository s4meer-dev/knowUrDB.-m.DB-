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
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10 w-full">
      <div className="flex items-center space-x-2">
        <h1 className="text-2xl font-bold text-indigo-600 tracking-tight">KnowUrDB</h1>
      </div>
      
      <div className="flex items-center space-x-4 text-sm bg-gray-50 px-4 py-2 rounded-full border border-gray-100">
        <div className="flex items-center space-x-2 border-r border-gray-200 pr-4">
          <span className="text-gray-500 font-medium">Backend:</span>
          {backendLoading ? (
            <span className="text-gray-500 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
              Checking
            </span>
          ) : health ? (
            <span className="text-green-600 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Connected
            </span>
          ) : (
            <span className="text-red-600 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              Disconnected
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-gray-500 font-medium">AI:</span>
          {backendLoading ? (
            <span className="text-gray-500 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
              Checking
            </span>
          ) : aiStatus?.status === 'ready' ? (
            <span className="text-indigo-600 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              Ready
            </span>
          ) : aiStatus?.configured === false ? (
            <span className="text-amber-600 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Unconfigured
            </span>
          ) : (
            <span className="text-red-600 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              Unavailable
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
