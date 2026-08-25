import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
import { SuggestionsPanel } from '../components/workspace/SuggestionsPanel';
import { QueryResult } from '../components/workspace/QueryResult';
import { EmptyState } from '../components/common/EmptyState';
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

  const handleQuery = async (q: string = question) => {
    if (!q.trim()) return;
    
    setQuestion(q);
    setLoading(true);
    
    try {
      const res = await queryDatabase(q);
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
        <div className="mb-10 text-center animate-slide-up">
          <h2 className="text-3xl font-bold text-zinc-900 tracking-tight mb-3">Explore your Database</h2>
          <p className="text-zinc-500 text-lg">Ask questions in plain English to instantly query and analyze your data.</p>
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

