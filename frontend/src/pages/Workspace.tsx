import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
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
          {/* Sleek Minimalist Icon Container */}
          <div className="relative mb-8 mt-2 group">
            <div className="w-16 h-16 bg-[#121214]/80 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.12)] relative transition-all duration-700 ease-out group-hover:shadow-[0_8px_30px_rgba(34,211,238,0.15)] group-hover:border-cyan-500/20 group-hover:bg-[#121214]/90">
               {/* Extremely subtle breathing glow inside */}
               <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/5 to-transparent rounded-2xl opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>

               <AnimatePresence mode="wait">
                 {textIndex === 0 ? (
                   <motion.svg
                     key="box-icon"
                     initial={{ opacity: 0, scale: 0.9, y: 5 }}
                     animate={{ opacity: 1, scale: 1, y: 0 }}
                     exit={{ opacity: 0, scale: 0.9, y: -5 }}
                     transition={{ duration: 0.4, ease: "easeOut" }}
                     className="w-7 h-7 text-cyan-400/90 relative z-10 transition-transform duration-700 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                   >
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                   </motion.svg>
                 ) : (
                   <motion.svg
                     key="smile-icon"
                     initial={{ opacity: 0, scale: 0.9, y: 5 }}
                     animate={{ opacity: 1, scale: 1, y: 0 }}
                     exit={{ opacity: 0, scale: 0.9, y: -5 }}
                     transition={{ duration: 0.4, ease: "easeOut" }}
                     className="w-7 h-7 text-cyan-400/90 relative z-10 transition-transform duration-700 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                   >
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" />
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" />
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 9H9.01" />
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 9H15.01" />
                   </motion.svg>
                 )}
               </AnimatePresence>
            </div>
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

      <div className={`relative z-20 transition-all duration-500 ease-in-out max-w-3xl mx-auto w-full ${result || loading ? 'mb-6' : 'mb-10 transform translate-y-4'}`}>
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

      <div className="flex-1">
        {(result || loading) && (
          <div className="animate-fade-in">
            <QueryResult 
              result={result} 
              isLoading={loading} 
              onFollowUp={(q, sourceIds) => handleQuery(q, sourceIds)} 
            />
          </div>
        )}
      </div>

      {/* Trademark - Fixed globally on this window only */}
      <div className="fixed bottom-5 right-6 z-50 pointer-events-none group">
        <div className="pointer-events-auto cursor-default flex flex-col items-end">
          <span className="text-zinc-600/40 text-[10px] font-mono tracking-[0.2em] uppercase transition-all duration-500 ease-out 
            group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-cyan-400 group-hover:to-purple-500 
            group-hover:tracking-[0.4em] group-hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.8)] relative"
          >
            ~by sameer ;)
            
            {/* Subtle underglow that expands on hover */}
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-cyan-400/50 shadow-[0_0_8px_rgba(34,211,238,1)] transition-all duration-500 group-hover:w-full opacity-0 group-hover:opacity-100"></div>
          </span>
        </div>
      </div>
    </div>
  );
};

