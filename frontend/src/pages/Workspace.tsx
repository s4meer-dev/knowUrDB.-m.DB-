import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
import { SuggestionsPanel } from '../components/workspace/SuggestionsPanel';
import { QueryResult } from '../components/workspace/QueryResult';
import TextType from '../components/TextType/TextType';

import { queryDatabase, getSources } from '../services/api';
import type { QueryResponse, SourceMetadata } from '../types';

export const Workspace: React.FC = () => {
  const location = useLocation();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string>('all');
  const [loadingSources, setLoadingSources] = useState(true);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setLoadingSources(true);
      const data = await getSources();
      setSources(data);
    } catch (e) {
      console.error("Failed to fetch sources", e);
    } finally {
      setLoadingSources(false);
    }
  };

  useEffect(() => {
    // Check if we came here from the History page with an initial question
    const state = location.state as { initialQuestion?: string, sourceId?: string };
    if (state?.initialQuestion && !loading && !result) {
      if (state.sourceId) {
        setSelectedSourceId(state.sourceId);
        handleQuery(state.initialQuestion, state.sourceId === 'all' ? undefined : [state.sourceId]);
      } else {
        handleQuery(state.initialQuestion);
      }
      // Clear the state so it doesn't trigger on reload
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleQuery = async (q: string = question, sourceIds?: string[]) => {
    if (!q.trim()) return;
    
    setQuestion(q);
    setLoading(true);
    
    // Use selectedSourceId if not explicitly provided
    const finalSourceIds = sourceIds || (selectedSourceId === 'all' ? undefined : [selectedSourceId]);
    
    try {
      const res = await queryDatabase(q, finalSourceIds);
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
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
             </svg>
          </div>
          <h2 className="text-4xl font-bold text-zinc-100 tracking-tight mb-4 min-h-[40px]">
            <TextType
              text={["Ask your database anything.", "Explore data in natural language.", "Unlock intelligent insights."]}
              typingSpeed={50}
              pauseDuration={2000}
              deletingSpeed={30}
              showCursor={true}
              cursorCharacter="|"
              cursorBlinkDuration={0.6}
              cursorClassName="text-cyan-400"
            />
          </h2>
        </div>
      )}

      <div className={`transition-all duration-500 ease-in-out max-w-3xl mx-auto w-full ${result || loading ? 'mb-6' : 'mb-10 transform translate-y-4'}`}>
        <QueryInput 
          value={question} 
          onChange={setQuestion} 
          onSubmit={() => handleQuery(question)} 
          isLoading={loading} 
          disabled={false} 
          sources={sources}
          selectedSourceId={selectedSourceId}
          onSourceChange={setSelectedSourceId}
          loadingSources={loadingSources}
        />
      </div>

      {!result && !loading && (
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <SuggestionsPanel 
            onSelectSuggestion={(q) => handleQuery(q)} 
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
              onFollowUp={(q) => handleQuery(q)} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

