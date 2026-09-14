import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
import { SuggestionsPanel } from '../components/workspace/SuggestionsPanel';
import { QueryResult } from '../components/workspace/QueryResult';
import TextType from '../components/TextType/TextType';
import { motion, AnimatePresence } from 'motion/react';

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
  const [textIndex, setTextIndex] = useState(0);

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
             <AnimatePresence mode="wait">
               {textIndex === 0 ? (
                 <motion.svg
                   key="box-icon"
                   initial={{ opacity: 0, scale: 0.8, rotate: -90 }}
                   animate={{ opacity: 1, scale: 1, rotate: 0 }}
                   exit={{ opacity: 0, scale: 0.8, rotate: 90 }}
                   transition={{ duration: 0.3 }}
                   className="w-8 h-8 text-cyan-400 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                 >
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                 </motion.svg>
               ) : (
                 <motion.svg
                   key="smile-icon"
                   initial={{ opacity: 0, scale: 0.8, rotate: -90 }}
                   animate={{ opacity: 1, scale: 1, rotate: 0 }}
                   exit={{ opacity: 0, scale: 0.8, rotate: 90 }}
                   transition={{ duration: 0.3 }}
                   className="w-8 h-8 text-cyan-400 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                 >
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" />
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" />
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 9H9.01" />
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 9H15.01" />
                 </motion.svg>
               )}
             </AnimatePresence>
          </div>
          <h2 className="text-4xl font-bold text-zinc-100 tracking-tight mb-4 min-h-[40px]">
            <TextType
              text={["Ask your database anything.", "hehehehehe :))"]}
              onIndexChange={setTextIndex}
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

