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
    <div className="flex flex-col h-full max-w-5xl mx-auto space-y-6">
      <div className="mb-2">
        <h2 className="text-2xl font-bold text-gray-800 tracking-tight">Explore Database</h2>
        <p className="text-gray-500 mt-1">Ask questions in plain English to instantly query and analyze your data.</p>
      </div>

      <QueryInput 
        value={question} 
        onChange={setQuestion} 
        onSubmit={() => handleQuery(question)} 
        isLoading={loading} 
        disabled={false} 
      />

      <SuggestionsPanel 
        onSelectSuggestion={handleQuery} 
        disabled={loading} 
      />

      <div className="flex-1">
        {result || loading ? (
          <QueryResult 
            result={result} 
            isLoading={loading} 
            onFollowUp={handleQuery} 
          />
        ) : (
          <div className="mt-8">
            <EmptyState 
              title="Ready to query" 
              message="Select a suggestion above or type your own question to explore the database." 
              icon={
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              }
            />
          </div>
        )}
      </div>
    </div>
  );
};

