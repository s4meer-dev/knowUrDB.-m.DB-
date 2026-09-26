import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { QueryInput } from '../components/workspace/QueryInput';
import { QueryResult } from '../components/workspace/QueryResult';
import TextType from '../components/TextType/TextType';
import { motion, AnimatePresence } from 'motion/react';

import { queryDatabase, getSources, activateSource } from '../services/api';
import type { QueryResponse, SourceMetadata, QueryScopeModel } from '../types';

type QueryMachineState =
  | 'IDLE'
  | 'PROCESSING'
  | 'CLARIFICATION_REQUIRED'
  | 'RESULT_READY'
  | 'EMPTY_RESULT'
  | 'ERROR';

interface SessionSnapshot {
  question: string;
  result: QueryResponse | null;
  conversationContext: Record<string, any>;
  machineState: QueryMachineState;
}

export const Workspace: React.FC = () => {
  const location = useLocation();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [machineState, setMachineState] = useState<QueryMachineState>('IDLE');

  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string>(() => {
    const stateSourceId = (location.state as { sourceId?: string } | null)?.sourceId;
    return stateSourceId || 'all';
  });
  const [activeCollection, setActiveCollection] = useState<string | null>(null);
  const [conversationContext, setConversationContext] = useState<Record<string, any>>({});
  const [sessionStack, setSessionStack] = useState<SessionSnapshot[]>([]);
  const [loadingSources, setLoadingSources] = useState(true);
  const [textIndex, setTextIndex] = useState(0);

  // Race condition protection: monotonic request ID + AbortController
  const requestIdRef = useRef<number>(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchSources();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const fetchSources = async () => {
    try {
      setLoadingSources(true);
      const data = await getSources();
      setSources(data);
      const stateSourceId = (location.state as { sourceId?: string } | null)?.sourceId;
      if (stateSourceId && data.some((s) => s.source_id === stateSourceId)) {
        setSelectedSourceId(stateSourceId);
        activateSource(stateSourceId).catch(() => {});
      }
      // Critical Invariant (Bug #1 Fix): DEFAULT MUST ALWAYS BE ALL SOURCES.
      // There must be NO automatically selected dataset or collection on initial page load.
    } catch (e) {
      console.error('Failed to fetch sources', e);
    } finally {
      setLoadingSources(false);
    }
  };

  useEffect(() => {
    const state = location.state as { initialQuestion?: string; sourceId?: string } | null;
    if (state?.sourceId) {
      setSelectedSourceId(state.sourceId);
      localStorage.setItem('knowurdb_active_source_id', state.sourceId);
      activateSource(state.sourceId).catch(() => {});
      setConversationContext({});
      setResult(null);
      setMachineState('IDLE');
    }
    if (state?.initialQuestion && !loading) {
      handleQuery(
        state.initialQuestion,
        state.sourceId && state.sourceId !== 'all' ? [state.sourceId] : undefined
      );
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const pushCurrentToStack = () => {
    setSessionStack((prev) => [
      ...prev,
      {
        question,
        result,
        conversationContext,
        machineState,
      },
    ]);
  };

  const handleBack = () => {
    abortControllerRef.current?.abort();
    setLoading(false);

    if (sessionStack.length > 0) {
      const prevSnap = sessionStack[sessionStack.length - 1];
      setSessionStack((s) => s.slice(0, -1));
      setQuestion(prevSnap.question);
      setResult(prevSnap.result);
      setConversationContext(prevSnap.conversationContext);
      setMachineState(prevSnap.machineState);
    } else {
      // Return to clean IDLE state while preserving the user's typed question
      setResult(null);
      setMachineState('IDLE');
    }
  };

  const handleChangeCollection = () => {
    if (!result) return;
    pushCurrentToStack();

    const candidates =
      result.candidates && result.candidates.length > 0
        ? result.candidates
        : result.presentation?.candidate_collections || [];

    const clarificationResult: QueryResponse = {
      ...result,
      status: 'clarification_required',
      intent: 'CLARIFICATION',
      error: `Which collection would you like to use for "${result.question}"?`,
      candidates,
      presentation: {
        type: 'clarification',
        title: 'NEED A LITTLE MORE CONTEXT',
        summary: `Select the collection you would like to use for "${result.question}":`,
        candidate_collections: candidates,
      },
    };
    setResult(clarificationResult);
    setMachineState('CLARIFICATION_REQUIRED');
  };

  const handleSelectCollection = (collectionName: string, sourceId?: string) => {
    const baseQuestion =
      conversationContext.pending_question || result?.question || question;
    if (sourceId && selectedSourceId === 'all') {
      setSelectedSourceId(sourceId);
      activateSource(sourceId).catch(() => {});
    }
    setActiveCollection(collectionName);
    const srcIds = sourceId
      ? [sourceId]
      : selectedSourceId === 'all'
      ? undefined
      : [selectedSourceId];
    handleQuery(baseQuestion, srcIds, collectionName);
  };

  const handleSourceSwitch = (newSourceId: string) => {
    // Cancel any in-flight query and reset collection context (Section 40, 41)
    abortControllerRef.current?.abort();
    requestIdRef.current += 1;
    setLoading(false);
    setSelectedSourceId(newSourceId);
    setActiveCollection(null); // Clear selected collection when switching datasets
    if (newSourceId !== 'all') {
      activateSource(newSourceId).catch(() => {});
    }
    setConversationContext({});
    setSessionStack([]);
    setResult(null);
    setMachineState('IDLE');
  };

  const handleQuery = async (
    q: string = question,
    sourceIds?: string[],
    overrideCollection?: string
  ) => {
    const trimmed = q.trim();
    if (!trimmed) return;

    // Push previous non-empty state onto navigation stack so Back works seamlessly
    if (result) {
      pushCurrentToStack();
    }

    // Cancel any previous in-flight request (Section 43 & 44)
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    const currentReqId = ++requestIdRef.current;

    setQuestion(trimmed);
    setLoading(true);
    setMachineState('PROCESSING');

    const effectiveCollection = overrideCollection !== undefined ? overrideCollection : activeCollection;
    if (overrideCollection !== undefined) {
      setActiveCollection(overrideCollection);
    }

    const finalSourceIds =
      sourceIds || (selectedSourceId === 'all' ? undefined : [selectedSourceId]);

    const targetSrcId = finalSourceIds?.[0] || (selectedSourceId === 'all' ? null : selectedSourceId);
    const activeSrcMeta = targetSrcId ? sources.find((s) => s.source_id === targetSrcId) : null;

    const scopeObj: QueryScopeModel = {
      scope_type: !targetSrcId ? 'ALL_SOURCES' : (effectiveCollection ? 'COLLECTION' : 'DATASET'),
      dataset_id: targetSrcId,
      dataset_name: activeSrcMeta?.display_name || activeSrcMeta?.name || null,
      collection_name: effectiveCollection,
      database_name: activeSrcMeta?.database_name || null,
    };

    try {
      const res = await queryDatabase(
        trimmed,
        finalSourceIds,
        effectiveCollection || undefined,
        conversationContext,
        controller.signal,
        scopeObj
      );

      // Discard stale response if a newer query was launched
      if (currentReqId !== requestIdRef.current) return;

      setResult(res);

      if (res.status === 'clarification_required') {
        setMachineState('CLARIFICATION_REQUIRED');
        setConversationContext((prev) => ({
          ...prev,
          pending_question: trimmed,
          intent: res.query_plan?.intent || prev.intent,
        }));
      } else if (res.status === 'error') {
        setMachineState('ERROR');
      } else if (res.presentation?.type === 'empty') {
        setMachineState('EMPTY_RESULT');
        if (res.collection) {
          setConversationContext({
            collection: res.collection,
            last_question: trimmed,
            filters: res.query_plan?.filters || {},
            intent: res.intent,
          });
        }
      } else {
        setMachineState('RESULT_READY');
        if (res.collection) {
          setConversationContext({
            collection: res.collection,
            last_question: trimmed,
            filters: res.query_plan?.filters || {},
            intent: res.intent,
          });
        }
      }
    } catch (e: any) {
      if (e?.name === 'CanceledError' || e?.code === 'ERR_CANCELED') {
        return;
      }
      if (currentReqId !== requestIdRef.current) return;

      setMachineState('ERROR');
      setResult({
        question: trimmed,
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0,
        status: 'error',
        error:
          e?.response?.data?.detail ||
          e.message ||
          "I couldn't complete that request.",
      });
    } finally {
      if (currentReqId === requestIdRef.current) {
        setLoading(false);
      }
    }
  };

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

      {/* Main Minimal Query Interface: Dataset Selector + Question Box ONLY (No collection chips, no automatic suggestions) */}
      <div
        className={`relative z-20 transition-all duration-300 ease-out max-w-3xl mx-auto w-full ${
          result || loading ? 'mb-2' : 'mb-8 transform translate-y-2'
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
          onSourceChange={handleSourceSwitch}
          loadingSources={loadingSources}
          activeCollection={activeCollection}
          onClearCollection={() => setActiveCollection(null)}
        />
      </div>

      <div className="flex-1">
        {(result || loading) && (
          <div className="animate-fade-in">
            <QueryResult
              result={result}
              isLoading={loading}
              canGoBack={true}
              onBack={handleBack}
              onChangeCollection={handleChangeCollection}
              onSelectCollection={handleSelectCollection}
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
