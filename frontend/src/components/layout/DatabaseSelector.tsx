import React, { useState, useEffect, useRef } from 'react';
import { getDatabaseStatus, uploadDatabase, resetDatabase } from '../../services/api';
import type { DatabaseStatusResponse } from '../../types';

export const DatabaseSelector: React.FC = () => {
  const [status, setStatus] = useState<DatabaseStatusResponse | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchStatus();
    
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await getDatabaseStatus();
      setStatus(data);
    } catch (err) {
      console.error("Failed to fetch database status", err);
    }
  };

  const handleReset = async () => {
    try {
      setIsUploading(true);
      await resetDatabase();
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reset database");
      setIsUploading(false);
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      setError(null);
      await uploadDatabase(file);
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || "Failed to upload database. Please ensure it's a valid supported format.");
      setIsUploading(false);
    }
  };

  if (!status) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-xs font-medium bg-zinc-900/50 hover:bg-zinc-800/80 transition-colors px-3 py-1.5 rounded-lg border border-zinc-800 backdrop-blur-md"
      >
        <div className={`w-2 h-2 rounded-full ${status.is_demo ? 'bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.5)]' : 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]'}`}></div>
        <span className="text-zinc-300 truncate max-w-[150px]">{status.name}</span>
        <svg className={`w-3 h-3 text-zinc-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-72 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden z-50 animate-fade-in origin-top-right">
          <div className="p-4 border-b border-zinc-800/50">
            <h3 className="text-sm font-semibold text-zinc-100 mb-1">Active Database</h3>
            <p className="text-xs text-zinc-400 break-all">{status.is_demo ? 'Using the default Demo Database' : status.path}</p>
            {!status.is_demo && status.format && (
              <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                <span className="px-2 py-0.5 bg-zinc-800 rounded-md text-zinc-300 border border-zinc-700/50">
                  Format: <span className="font-medium text-purple-400">{status.format}</span>
                </span>
                {status.table_count !== undefined && (
                  <span className="px-2 py-0.5 bg-zinc-800 rounded-md text-zinc-300 border border-zinc-700/50">
                    Tables: <span className="font-medium text-cyan-400">{status.table_count}</span>
                  </span>
                )}
                {status.record_count !== undefined && (
                  <span className="px-2 py-0.5 bg-zinc-800 rounded-md text-zinc-300 border border-zinc-700/50">
                    Records: <span className="font-medium text-emerald-400">{status.record_count}</span>
                  </span>
                )}
              </div>
            )}
          </div>
          
          <div className="p-3 space-y-2">
            {!status.is_demo && (
              <button 
                onClick={handleReset}
                disabled={isUploading}
                className="w-full flex items-center space-x-2 text-left px-3 py-2 text-sm text-zinc-300 hover:text-white hover:bg-zinc-800/50 rounded-lg transition-colors disabled:opacity-50"
              >
                <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span>Revert to Demo Database</span>
              </button>
            )}
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="w-full flex items-center space-x-2 text-left px-3 py-2 text-sm text-zinc-300 hover:text-white hover:bg-zinc-800/50 rounded-lg transition-colors disabled:opacity-50 group"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                {isUploading ? (
                   <span className="w-4 h-4 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></span>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <div className="font-medium text-zinc-200">{isUploading ? "Processing..." : "Upload Database"}</div>
                <div className="text-[10px] text-zinc-500">SQL, CSV, Excel, JSON, SQLite, Parquet</div>
              </div>
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".db,.sqlite,.sqlite3,.sql,.csv,.tsv,.json,.jsonl,.xlsx,.xls,.parquet,.duckdb" 
              onChange={handleFileChange} 
            />
          </div>
          
          {error && (
            <div className="px-4 py-3 bg-red-500/10 border-t border-red-500/20 text-xs text-red-400">
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
