import React, { useEffect, useState, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSources, deleteSource, generateDemoDatabase, activateSource } from '../services/api';
import type { SourceMetadata } from '../types';
import { MultiUpload } from '../components/workspace/MultiUpload';
import { CustomDropdown } from '../components/common/CustomDropdown';

type GenerationState =
  | 'IDLE'
  | 'GENERATING'
  | 'VALIDATING'
  | 'REGISTERING'
  | 'COMPLETE'
  | 'FAILED';

const GENERATION_STAGES = [
  'SELECTING DOMAIN',
  'BUILDING SCHEMA',
  'CREATING DATABASE',
  'POPULATING COLLECTIONS',
  'INDEXING',
  'VERIFYING',
  'READY',
];

export const SourceLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  const [genState, setGenState] = useState<GenerationState>('IDLE');
  const [genStageIndex, setGenStageIndex] = useState<number>(0);
  const [genError, setGenError] = useState<string | null>(null);
  const [lastCreatedSource, setLastCreatedSource] = useState<SourceMetadata | null>(null);
  const isGeneratingRef = useRef(false);

  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(() => {
    return localStorage.getItem('knowurdb_active_source_id');
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<string>('recent');

  const selectAndActivateSource = async (sourceId: string | null) => {
    setSelectedSourceId(sourceId);
    if (sourceId) {
      localStorage.setItem('knowurdb_active_source_id', sourceId);
      try {
        await activateSource(sourceId);
      } catch {
        // Ignore activation sync error
      }
    } else {
      localStorage.removeItem('knowurdb_active_source_id');
    }
  };

  const loadSources = async (preferSourceId?: string) => {
    try {
      const data = await getSources();
      setSources(data);
      if (preferSourceId && data.some((s) => s.source_id === preferSourceId)) {
        await selectAndActivateSource(preferSourceId);
      } else if (
        selectedSourceId &&
        data.some((s) => s.source_id === selectedSourceId)
      ) {
        // Keep current selection
      } else if (data.length > 0) {
        await selectAndActivateSource(data[0].source_id);
      } else {
        setSelectedSourceId(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteSource(id);
      const remaining = sources.filter((s) => s.source_id !== id);
      setSources(remaining);
      if (lastCreatedSource?.source_id === id) {
        setLastCreatedSource(null);
      }
      if (selectedSourceId === id) {
        const nextId = remaining.length > 0 ? remaining[0].source_id : null;
        await selectAndActivateSource(nextId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateDemo = async () => {
    if (isGeneratingRef.current) return;
    isGeneratingRef.current = true;
    setGenError(null);
    setGenState('GENERATING');
    setGenStageIndex(0);

    const stageTimer = window.setInterval(() => {
      setGenStageIndex((prev) => (prev < 5 ? prev + 1 : prev));
    }, 110);

    try {
      const newSource = await generateDemoDatabase();
      window.clearInterval(stageTimer);
      setGenState('VALIDATING');
      setGenStageIndex(5);
      await loadSources(newSource.source_id);
      setGenState('COMPLETE');
      setGenStageIndex(6);
      setLastCreatedSource(newSource);
    } catch (e: any) {
      window.clearInterval(stageTimer);
      console.error('Failed to generate demo database:', e);
      const errMsg =
        e?.response?.data?.detail?.message ||
        e?.response?.data?.detail ||
        e?.message ||
        'Unable to connect to MongoDB or provision collections.';
      setGenError(String(errMsg));
      setGenState('FAILED');
    } finally {
      isGeneratingRef.current = false;
    }
  };

  const formatSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let l = 0,
      n = bytes || 0;
    while (n >= 1024 && ++l) n = n / 1024;
    return n.toFixed(n < 10 && l > 0 ? 1 : 0) + ' ' + units[l];
  };

  const filteredAndSortedSources = useMemo(() => {
    let result = [...sources];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          (s.display_name && s.display_name.toLowerCase().includes(q)) ||
          (s.database_name && s.database_name.toLowerCase().includes(q)) ||
          (s.domain && s.domain.toLowerCase().includes(q))
      );
    }
    if (statusFilter !== 'all') {
      result = result.filter((s) => s.status === statusFilter);
    }
    if (typeFilter !== 'all') {
      result = result.filter((s) => s.detected_format === typeFilter);
    }
    result.sort((a, b) => {
      if (sortOrder === 'recent')
        return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
      if (sortOrder === 'oldest')
        return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime();
      if (sortOrder === 'name') return a.name.localeCompare(b.name);
      if (sortOrder === 'size') return b.size_bytes - a.size_bytes;
      if (sortOrder === 'records') return (b.record_count || 0) - (a.record_count || 0);
      return 0;
    });
    return result;
  }, [sources, searchQuery, statusFilter, typeFilter, sortOrder]);

  const selectedSource = useMemo(() => {
    return sources.find((s) => s.source_id === selectedSourceId);
  }, [sources, selectedSourceId]);

  const availableTypes = useMemo(() => {
    const types = new Set(sources.map((s) => s.detected_format));
    return Array.from(types).filter(Boolean);
  }, [sources]);

  const isGenerating =
    genState === 'GENERATING' || genState === 'VALIDATING' || genState === 'REGISTERING';

  return (
    <div className="h-full flex flex-col animate-fade-in relative max-w-7xl mx-auto pb-6">
      <div className="mb-6 flex-shrink-0">
        <h1 className="text-3xl font-bold text-zinc-100 tracking-tight mb-2">
          MongoDB Source Library
        </h1>
        <p className="text-zinc-400">
          Generate independent multi-domain MongoDB databases or upload CSV, JSON, Excel, Parquet, and PDF files into indexed MongoDB collections.
        </p>
      </div>

      <div className="mb-6 flex-shrink-0 flex flex-col gap-4">
        <MultiUpload onUploadSuccess={() => loadSources()} />
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={handleGenerateDemo}
            disabled={isGenerating}
            aria-label="Generate Random MongoDB Demo Dataset"
            className="text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-all flex items-center gap-2.5 px-6 py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/25 shadow-[0_0_18px_rgba(34,211,238,0.12)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                ></path>
              </svg>
            )}
            {isGenerating
              ? 'Generating Independent MongoDB Dataset...'
              : 'Generate Random MongoDB Demo Dataset'}
          </button>

          {/* Cinematic Generation Progress Panel */}
          {isGenerating && (
            <div className="w-full max-w-2xl bg-zinc-900/90 border border-cyan-500/30 rounded-2xl p-5 shadow-[0_0_30px_rgba(6,182,212,0.12)] animate-fade-in">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-widest text-cyan-400">
                  GENERATING DEMO DATASET
                </span>
                <span className="text-xs font-mono text-zinc-400">
                  {GENERATION_STAGES[genStageIndex]}
                </span>
              </div>
              <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-200"
                  style={{
                    width: `${Math.min(100, Math.round(((genStageIndex + 1) / GENERATION_STAGES.length) * 100))}%`,
                  }}
                />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {GENERATION_STAGES.slice(0, 6).map((stageLabel, idx) => {
                  const done = idx < genStageIndex;
                  const active = idx === genStageIndex;
                  return (
                    <div
                      key={stageLabel}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border ${
                        done
                          ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300'
                          : active
                          ? 'bg-cyan-500/15 border-cyan-500/35 text-cyan-200'
                          : 'bg-zinc-950/40 border-zinc-800/60 text-zinc-500'
                      }`}
                    >
                      <span>{done ? '✓' : active ? '●' : '○'}</span>
                      <span className="truncate font-medium">{stageLabel}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Dataset Created Result Banner */}
          {genState === 'COMPLETE' && lastCreatedSource && !isGenerating && (
            <div className="w-full max-w-3xl bg-zinc-900/90 border border-emerald-500/30 rounded-2xl p-5 shadow-[0_0_25px_rgba(16,185,129,0.1)] animate-fade-in">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      DATASET CREATED
                    </span>
                    {lastCreatedSource.domain && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                        {lastCreatedSource.domain}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-bold text-zinc-100">
                    {lastCreatedSource.display_name || lastCreatedSource.name}
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5 font-mono">
                    MongoDB database:{' '}
                    <span className="text-cyan-300">{lastCreatedSource.database_name}</span> •{' '}
                    <span className="text-zinc-200">
                      {lastCreatedSource.table_count || lastCreatedSource.collections?.length || 5}{' '}
                      collections
                    </span>{' '}
                    •{' '}
                    <span className="text-zinc-200">
                      {(lastCreatedSource.record_count || 0).toLocaleString()} documents
                    </span>
                  </p>
                </div>
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() =>
                      navigate('/', { state: { sourceId: lastCreatedSource.source_id } })
                    }
                    className="bg-cyan-500 hover:bg-cyan-400 text-zinc-950 text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-[0_0_12px_rgba(34,211,238,0.2)]"
                  >
                    Query Dataset
                  </button>
                  <button
                    onClick={() =>
                      navigate('/schema', { state: { sourceId: lastCreatedSource.source_id } })
                    }
                    className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-semibold px-4 py-2 rounded-xl border border-zinc-700 transition-colors"
                  >
                    Explore BSON Schema
                  </button>
                  <button
                    onClick={() => setGenState('IDLE')}
                    className="text-zinc-500 hover:text-zinc-300 text-xs px-2 py-1"
                    title="Dismiss"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Dataset Generation Error Panel */}
          {genState === 'FAILED' && genError && (
            <div className="w-full max-w-2xl bg-red-950/30 border border-red-500/30 rounded-2xl p-4 flex items-center justify-between gap-4 animate-fade-in">
              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-red-400 mb-0.5">
                  DATASET GENERATION FAILED
                </div>
                <div className="text-xs text-zinc-300">{genError}</div>
              </div>
              <button
                onClick={handleGenerateDemo}
                className="px-4 py-2 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/30 text-xs font-semibold transition-colors"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
        </div>
      ) : sources.length === 0 ? (
        <div className="flex-1 bg-zinc-900/30 border border-zinc-800/50 rounded-2xl flex flex-col items-center justify-center p-12 text-center shadow-xl">
          <h3 className="text-xl font-bold text-zinc-100 mb-2">No MongoDB sources yet</h3>
          <p className="text-zinc-400 max-w-sm mb-6">
            Click Generate Random MongoDB Demo Dataset or upload a file above to create indexed MongoDB collections.
          </p>
        </div>
      ) : (
        <div className="flex-1 flex gap-6 min-h-0">
          {/* Left Sidebar: Source List & Filters */}
          <div className="w-[390px] flex flex-col gap-4 flex-shrink-0">
            <div className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-4 shadow-lg flex flex-col gap-3">
              <div className="relative">
                <svg
                  className="absolute left-3 top-2.5 w-5 h-5 text-zinc-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  ></path>
                </svg>
                <input
                  type="text"
                  placeholder="Search MongoDB databases & sources..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-950/50 border border-zinc-800/80 rounded-xl pl-10 pr-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                />
              </div>
              <div className="flex gap-2">
                <CustomDropdown
                  value={statusFilter}
                  onChange={setStatusFilter}
                  options={[
                    { value: 'all', label: 'All Status' },
                    { value: 'ready', label: 'Ready' },
                    { value: 'failed', label: 'Failed' },
                  ]}
                  triggerClassName="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-3 py-2 text-xs text-zinc-300 hover:text-zinc-100 transition-colors flex-1"
                />
                <CustomDropdown
                  value={typeFilter}
                  onChange={setTypeFilter}
                  options={[
                    { value: 'all', label: 'All Types' },
                    ...availableTypes.map((t) => ({ value: t, label: t.toUpperCase() })),
                  ]}
                  triggerClassName="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-3 py-2 text-xs text-zinc-300 hover:text-zinc-100 transition-colors flex-1"
                />
                <CustomDropdown
                  value={sortOrder}
                  onChange={setSortOrder}
                  options={[
                    { value: 'recent', label: 'Recent' },
                    { value: 'oldest', label: 'Oldest' },
                    { value: 'name', label: 'Name' },
                    { value: 'size', label: 'Size' },
                  ]}
                  triggerClassName="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-3 py-2 text-xs text-zinc-300 hover:text-zinc-100 transition-colors flex-1"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar pb-6">
              {filteredAndSortedSources.map((source) => {
                const isMongoSource =
                  source.source_category === 'mongodb' || source.detected_format === 'mongodb';
                const cardTitle = source.display_name || source.name;
                const colCount = source.table_count || source.collections?.length || 0;
                return (
                  <button
                    key={source.source_id}
                    onClick={() => selectAndActivateSource(source.source_id)}
                    className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                      selectedSourceId === source.source_id
                        ? 'bg-cyan-500/10 border-cyan-500/35 shadow-[0_0_15px_rgba(34,211,238,0.06)]'
                        : 'bg-zinc-900/40 border-zinc-800/60 hover:bg-zinc-800/40 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            selectedSourceId === source.source_id
                              ? 'bg-cyan-500/20 text-cyan-400'
                              : 'bg-zinc-800 text-zinc-400'
                          }`}
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                            ></path>
                          </svg>
                        </div>
                        <div className="truncate">
                          <h4
                            className={`font-semibold truncate ${
                              selectedSourceId === source.source_id
                                ? 'text-zinc-100'
                                : 'text-zinc-300'
                            }`}
                          >
                            {cardTitle}
                          </h4>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                              {isMongoSource ? 'MONGODB' : 'UPLOADED FILE'}
                            </span>
                            {source.domain && (
                              <span className="text-[10px] uppercase tracking-wider text-zinc-400">
                                • {source.domain}
                              </span>
                            )}
                            {source.database_name && (
                              <span className="text-[10px] font-mono text-emerald-400/90 truncate">
                                • {source.database_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex-shrink-0 ml-2 mt-1">
                        <div
                          className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                          title="Ready"
                        ></div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-3 text-xs text-zinc-400 font-medium px-1">
                      <span>{colCount} collections</span>
                      <span>•</span>
                      <span>{(source.record_count || 0).toLocaleString()} docs</span>
                      <div className="ml-auto opacity-70">{formatSize(source.size_bytes)}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Detail Panel */}
          <div className="flex-1 bg-zinc-900/30 backdrop-blur-md border border-zinc-800/80 rounded-2xl shadow-xl flex flex-col overflow-hidden relative">
            {selectedSource ? (
              <div className="h-full flex flex-col overflow-y-auto custom-scrollbar relative z-10 animate-fade-in">
                <div className="min-h-32 bg-zinc-800/30 border-b border-zinc-800/80 relative flex items-end p-8">
                  <div className="flex items-center gap-5 w-full relative z-10">
                    <div className="w-16 h-16 bg-zinc-900 border border-zinc-700/50 rounded-2xl flex items-center justify-center shadow-lg text-cyan-400 flex-shrink-0">
                      <svg
                        className="w-8 h-8"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.5"
                          d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                        ></path>
                      </svg>
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <h2 className="text-2xl font-bold text-zinc-100 truncate">
                        {selectedSource.display_name || selectedSource.name}
                      </h2>
                      {selectedSource.description && (
                        <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                          {selectedSource.description}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-2.5 mt-2.5 text-sm font-medium">
                        <span className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {selectedSource.status}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                          {selectedSource.source_category === 'uploaded_file'
                            ? `UPLOADED FILE (${selectedSource.detected_format.toUpperCase()})`
                            : 'MONGODB'}
                        </span>
                        {selectedSource.domain && (
                          <span className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-zinc-800 text-zinc-300 border border-zinc-700">
                            {selectedSource.domain}
                          </span>
                        )}
                        {selectedSource.database_name && (
                          <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-zinc-900 text-cyan-300 border border-cyan-500/25">
                            MongoDB: {selectedSource.database_name}
                          </span>
                        )}
                        <span className="text-zinc-500 text-xs border-l border-zinc-700 pl-3">
                          Created {new Date(selectedSource.uploaded_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-8 border-b border-zinc-800/50 flex flex-wrap gap-4">
                  <button
                    onClick={() => {
                      localStorage.setItem('knowurdb_active_source_id', selectedSource.source_id);
                      navigate('/', { state: { sourceId: selectedSource.source_id } });
                    }}
                    className="bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-semibold px-5 py-2.5 rounded-xl transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)] flex items-center gap-2"
                  >
                    Query Collection
                  </button>
                  <button
                    onClick={() => {
                      localStorage.setItem('knowurdb_active_source_id', selectedSource.source_id);
                      navigate('/schema', { state: { sourceId: selectedSource.source_id } });
                    }}
                    className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold px-5 py-2.5 rounded-xl transition-colors border border-zinc-700 flex items-center gap-2"
                  >
                    Explore BSON Schema
                  </button>
                  <button
                    onClick={() => handleDelete(selectedSource.source_id)}
                    className="ml-auto bg-red-500/10 hover:bg-red-500/20 text-red-400 font-medium px-4 py-2.5 rounded-xl transition-colors border border-red-500/20 flex items-center gap-2"
                  >
                    Delete Source
                  </button>
                </div>

                <div className="p-8 space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="bg-zinc-950/50 border border-zinc-800/80 p-5 rounded-xl">
                      <div className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-1">
                        MongoDB Documents
                      </div>
                      <div className="text-2xl font-bold text-zinc-100">
                        {selectedSource.record_count !== undefined
                          ? selectedSource.record_count.toLocaleString()
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-zinc-950/50 border border-zinc-800/80 p-5 rounded-xl">
                      <div className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-1">
                        Collections
                      </div>
                      <div className="text-2xl font-bold text-zinc-100">
                        {selectedSource.table_count || selectedSource.collections?.length || 1}
                      </div>
                    </div>
                    <div className="bg-zinc-950/50 border border-zinc-800/80 p-5 rounded-xl">
                      <div className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-1">
                        MongoDB Database
                      </div>
                      <div className="text-base font-mono font-bold text-cyan-300 truncate mt-1">
                        {selectedSource.database_name || 'knowurdb'}
                      </div>
                    </div>
                  </div>

                  {selectedSource.collections && selectedSource.collections.length > 0 && (
                    <div>
                      <h4 className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-3">
                        MongoDB Collections
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedSource.collections.map((col) => {
                          const cnt = selectedSource.collection_counts?.[col];
                          return (
                            <span
                              key={col}
                              className="px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-2"
                            >
                              <span>db.{col}</span>
                              {cnt !== undefined && (
                                <span className="text-[10px] text-emerald-400/70 bg-emerald-950/60 px-1.5 py-0.5 rounded">
                                  {cnt} docs
                                </span>
                              )}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {selectedSource.schema_summary && (
                    <div>
                      <h4 className="text-xs text-zinc-500 font-bold uppercase tracking-wider mb-3">
                        Collection & BSON Schema Summary
                      </h4>
                      <div className="bg-zinc-950/80 border border-zinc-800/80 rounded-xl p-4 font-mono text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto custom-scrollbar">
                        {typeof selectedSource.schema_summary === 'string'
                          ? selectedSource.schema_summary
                          : JSON.stringify(selectedSource.schema_summary, null, 2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-zinc-500">
                Select a MongoDB source to view collection details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
