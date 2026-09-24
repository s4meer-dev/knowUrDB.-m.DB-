import React, { useState, useEffect, useMemo } from 'react';
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
  const [activeCollection, setActiveCollection] = useState<string>('');
  const [conversationContext, setConversationContext] = useState<Record<string, any>>({});
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
      console.error('Failed to fetch sources', e);
    } finally {
      setLoadingSources(false);
    }
  };

  // Available collections for the active source
  const availableCollections = useMemo(() => {
    const activeSrc =
      selectedSourceId === 'all'
        ? sources[0]
        : sources.find((s) => s.source_id === selectedSourceId) || sources[0];
    return activeSrc?.collections || [];
  }, [sources, selectedSourceId]);

  useEffect(() => {
    const state = location.state as { initialQuestion?: string; sourceId?: string };
    if (state?.initialQuestion && !loading && !result) {
      if (state.sourceId) {
        setSelectedSourceId(state.sourceId);
        handleQuery(state.initialQuestion, state.sourceId === 'all' ? undefined : [state.sourceId]);
      } else {
        handleQuery(state.initialQuestion);
      }
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleQuery = async (
    q: string = question,
    sourceIds?: string[],
    overrideCollection?: string
  ) => {
    if (!q.trim()) return;

    setQuestion(q);
    setLoading(true);

    const finalSourceIds =
      sourceIds || (selectedSourceId === 'all' ? undefined : [selectedSourceId]);
    const targetCol =
      overrideCollection !== undefined
        ? overrideCollection
        : activeCollection || undefined;

    try {
      const res = await queryDatabase(q, finalSourceIds, targetCol, conversationContext);
      setResult(res);
      if (res.collection) {
        setConversationContext({
          collection: res.collection,
          filters: res.query_plan?.filters || {},
          intent: res.intent,
        });
      }
    } catch (e: any) {
      setResult({
        question: q,
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0,
        status: 'error',
        error: e?.response?.data?.detail || e.message || 'An unexpected error occurred.',
      });
    } finally {
      setLoading(false);
    }
  };

  const quickExamples = [
    'Give me info about dataset',
    'Show me data related to product',
    'What is the most expensive product?',
    'Show customers from Bangalore',
    'Compare products by price and units sold',
  ];

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto pt-8 pb-12 animate-fade-in">
      {!result && !loading && (
        <div className="mb-10 text-center animate-slide-up flex flex-col items-center">
          <div className="relative mb-7 mt-2 group">
            <div className="w-16 h-16 bg-[#121214]/80 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.12)] relative transition-all duration-700 ease-out group-hover:shadow-[0_8px_30px_rgba(34,211,238,0.15)] group-hover:border-cyan-500/20 group-hover:bg-[#121214]/90">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/5 to-transparent rounded-2xl opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>

              <AnimatePresence mode="wait">
                <motion.svg
                  key={textIndex}
                  initial={{ opacity: 0, scale: 0.9, y: 5 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -5 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                  className="w-7 h-7 text-cyan-400/90 relative z-10 transition-transform duration-700 group-hover:scale-110"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                  />
                </motion.svg>
              </AnimatePresence>
            </div>
          </div>
          <h2 className="text-4xl font-bold text-zinc-100 tracking-tight mb-3 min-h-[44px]">
            <TextType
              text={[
                'Ask your MongoDB collections anything.',
                'Natural language to Aggregation Pipelines.',
                'Multi-source intelligence & Vector RAG.',
              ]}
              onIndexChange={setTextIndex}
              typingSpeed={45}
              pauseDuration={2400}
              deletingSpeed={25}
              showCursor={true}
              cursorCharacter="|"
              cursorBlinkDuration={0.6}
              cursorClassName="text-cyan-400"
            />
          </h2>
          <p className="text-zinc-400 text-sm max-w-xl">
            Query BSON collections, nested documents, arrays, and unstructured PDFs using plain English—powered by read-only MongoDB aggregation pipelines.
          </p>
        </div>
      )}

      <div
        className={`relative z-20 transition-all duration-500 ease-in-out max-w-3xl mx-auto w-full ${
          result || loading ? 'mb-4' : 'mb-8 transform translate-y-2'
        }`}
      >
        <QueryInput
          value={question}
          onChange={setQuestion}
          onSubmit={() => handleQuery(question)}
          isLoading={loading}
          disabled={false}
          sources={sources}
          selectedSourceId={selectedSourceId}
          onSourceChange={(id) => {
            setSelectedSourceId(id);
            setActiveCollection('');
          }}
          loadingSources={loadingSources}
        />

        {/* Active Collection Context Selector Pills */}
        {availableCollections.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5 px-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mr-1">
              Collection:
            </span>
            <button
              type="button"
              onClick={() => setActiveCollection('')}
              className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border transition-all ${
                activeCollection === ''
                  ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                  : 'bg-zinc-900/50 text-zinc-400 border-zinc-800 hover:text-zinc-200'
              }`}
            >
              Auto-detect
            </button>
            {availableCollections.map((col) => (
              <button
                key={col}
                type="button"
                onClick={() => setActiveCollection(col === activeCollection ? '' : col)}
                className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border transition-all ${
                  activeCollection === col
                    ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                    : 'bg-zinc-900/50 text-zinc-400 border-zinc-800 hover:text-zinc-200'
                }`}
              >
                {col}
              </button>
            ))}
          </div>
        )}

        {!result && !loading && (
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            {quickExamples.map((ex) => (
              <button
                key={ex}
                onClick={() => handleQuery(ex)}
                className="text-xs text-zinc-400 hover:text-cyan-300 bg-zinc-900/60 hover:bg-cyan-500/10 border border-zinc-800 hover:border-cyan-500/30 px-3.5 py-2 rounded-xl transition-all duration-200"
              >
                {ex}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1">
        {(result || loading) && (
          <div className="animate-fade-in">
            <QueryResult
              result={result}
              isLoading={loading}
              onFollowUp={(q, sourceIds, overrideCol) =>
                handleQuery(q, sourceIds, overrideCol)
              }
            />
          </div>
        )}
      </div>

      <div className="fixed bottom-5 right-6 z-50 pointer-events-none group">
        <div className="pointer-events-auto cursor-default flex flex-col items-end">
          <span
            className="text-zinc-600/40 text-[10px] font-mono tracking-[0.2em] uppercase transition-all duration-500 ease-out 
            group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-cyan-400 group-hover:to-emerald-400 
            group-hover:tracking-[0.4em] group-hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.8)] relative"
          >
            knowUrDB (m.DB) ~ by sameer
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-cyan-400/50 shadow-[0_0_8px_rgba(34,211,238,1)] transition-all duration-500 group-hover:w-full opacity-0 group-hover:opacity-100"></div>
          </span>
        </div>
      </div>
    </div>
  );
};
