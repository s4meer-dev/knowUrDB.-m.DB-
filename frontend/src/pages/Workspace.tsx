import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
import { SuggestionsPanel } from '../components/workspace/SuggestionsPanel';
import { QueryResult } from '../components/workspace/QueryResult';

import { queryDatabase } from '../services/api';
import type { QueryResponse } from '../types';

export const Workspace: React.FC = () => {
  const location = useLocation();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);

  useEffect(() => {
    // Check if we came here from the History page with an initial question
    const state = location.state as { initialQuestion?: string };
    if (state?.initialQuestion && !loading && !result) {
      handleQuery(state.initialQuestion);
      // Clear the state so it doesn't trigger on reload
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleQuery = async (q: string = question, sourceIds?: string[]) => {
    if (!q.trim()) return;
    
    setQuestion(q);
    setLoading(true);
    
    try {
      const res = await queryDatabase(q, sourceIds);
      setResult(res);
    } catch (e: any) {
      setResult({
        question: q,
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0,
        status: 'error',
        error: e?.response?.data?.detail || e.message || 'An unexpected error occurred.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto pt-8 pb-12 animate-fade-in">
      {!result && !loading && (
        <div className="mb-12 text-center animate-slide-up flex flex-col items-center">
          <div className="w-16 h-16 bg-cyan-500/10 rounded-2xl flex items-center justify-center mb-6 border border-cyan-500/20 shadow-[0_0_30px_rgba(34,211,238,0.15)] relative overflow-hidden">
             <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/20 to-transparent"></div>
             <svg className="w-8 h-8 text-cyan-400 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
             </svg>
          </div>
          <h2 className="text-4xl font-bold text-zinc-100 tracking-tight mb-4">Ask your database anything.</h2>
          <p className="text-zinc-400 text-lg max-w-lg">Explore your connected data using natural language.</p>
        </div>
      )}

      <div className={`transition-all duration-500 ease-in-out ${result || loading ? 'mb-6' : 'mb-10 transform translate-y-4'}`}>
        <QueryInput 
          value={question} 
          onChange={setQuestion} 
          onSubmit={() => handleQuery(question)} 
          isLoading={loading} 
          disabled={false} 
        />
      </div>

      {!result && !loading && (
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <SuggestionsPanel 
            onSelectSuggestion={handleQuery} 
            disabled={loading} 
          />
        </div>
      )}

      <div className="flex-1">
        {(result || loading) && (
          <div className="animate-fade-in">
            <QueryResult 
              result={result} 
              isLoading={loading} 
              onFollowUp={handleQuery} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

