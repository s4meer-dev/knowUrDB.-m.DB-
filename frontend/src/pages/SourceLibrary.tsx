import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSources, deleteSource } from '../services/api';
import type { SourceMetadata } from '../types';
import { MultiUpload } from '../components/workspace/MultiUpload';

export const SourceLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Selection and filtering state
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<string>('recent');

  const loadSources = async () => {
    try {
      const data = await getSources();
      setSources(data);
      // Auto-select first source if none selected
      if (!selectedSourceId && data.length > 0) {
        setSelectedSourceId(data[0].source_id);
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
      const newSources = sources.filter(s => s.source_id !== id);
      setSources(newSources);
      if (selectedSourceId === id) {
        setSelectedSourceId(newSources.length > 0 ? newSources[0].source_id : null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const formatSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let l = 0, n = bytes || 0;
    while (n >= 1024 && ++l) n = n / 1024;
    return (n.toFixed(n < 10 && l > 0 ? 1 : 0) + ' ' + units[l]);
  };

  const filteredAndSortedSources = useMemo(() => {
    let result = [...sources];
    
    // Search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(s => s.name.toLowerCase().includes(q));
    }
    
    // Status Filter
    if (statusFilter !== 'all') {
      result = result.filter(s => s.status === statusFilter);
    }

    // Type Filter
    if (typeFilter !== 'all') {
      result = result.filter(s => s.detected_format === typeFilter);
    }

    // Sort
    result.sort((a, b) => {
      if (sortOrder === 'recent') return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
      if (sortOrder === 'oldest') return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime();
      if (sortOrder === 'name') return a.name.localeCompare(b.name);
      if (sortOrder === 'size') return b.size_bytes - a.size_bytes;
      if (sortOrder === 'records') return (b.record_count || 0) - (a.record_count || 0);
      return 0;
    });

    return result;
  }, [sources, searchQuery, statusFilter, typeFilter, sortOrder]);

  const selectedSource = useMemo(() => {
    return sources.find(s => s.source_id === selectedSourceId);
  }, [sources, selectedSourceId]);

  // Derive unique types for filter dropdown
  const availableTypes = useMemo(() => {
    const types = new Set(sources.map(s => s.detected_format));
    return Array.from(types).filter(Boolean);
  }, [sources]);

  return (
    <div className="h-full flex flex-col animate-fade-in relative max-w-7xl mx-auto pb-6">
      <div className="mb-6 flex-shrink-0">
        <h1 className="text-3xl font-bold text-zinc-100 tracking-tight mb-2">Knowledge Base</h1>
        <p className="text-zinc-400">Manage your connected databases, datasets, and documents.</p>
      </div>

      <div className="mb-6 flex-shrink-0">
        <MultiUpload onUploadSuccess={() => loadSources()} />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
        </div>
      ) : sources.length === 0 ? (
        <div className="flex-1 bg-zinc-900/30 border border-zinc-800/50 rounded-2xl flex flex-col items-center justify-center p-12 text-center shadow-xl">
          <div className="w-20 h-20 bg-zinc-800/50 rounded-full flex items-center justify-center text-zinc-500 mb-6 border border-zinc-700/50">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
          </div>
          <h3 className="text-xl font-bold text-zinc-100 mb-2">No sources yet</h3>
          <p className="text-zinc-400 max-w-sm mb-6">Upload your first database, CSV, or document above to start asking questions.</p>
        </div>
      ) : (
        <div className="flex-1 flex gap-6 min-h-0">
          
          {/* Left Sidebar: List & Filters */}
          <div className="w-[380px] flex flex-col gap-4 flex-shrink-0">
            <div className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-4 shadow-lg flex flex-col gap-3">
              <div className="relative">
                <svg className="absolute left-3 top-2.5 w-5 h-5 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                <input
                  type="text"
                  placeholder="Search sources..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-950/50 border border-zinc-800/80 rounded-xl pl-10 pr-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                />
              </div>
              <div className="flex gap-2">
                <select 
                  value={statusFilter} 
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-cyan-500 flex-1 cursor-pointer"
                >
                  <option value="all">All Status</option>
                  <option value="ready">Ready</option>
                  <option value="failed">Failed</option>
                </select>
                <select 
                  value={typeFilter} 
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-cyan-500 flex-1 cursor-pointer"
                >
                  <option value="all">All Types</option>
                  {availableTypes.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                </select>
                <select 
                  value={sortOrder} 
                  onChange={(e) => setSortOrder(e.target.value)}
                  className="bg-zinc-950/50 border border-zinc-800/80 rounded-lg px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-cyan-500 flex-1 cursor-pointer"
                >
                  <option value="recent">Recent</option>
                  <option value="oldest">Oldest</option>
                  <option value="name">Name</option>
                  <option value="size">Size</option>
                </select>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar pb-6">
              {filteredAndSortedSources.length === 0 ? (
                <div className="text-center p-8 text-zinc-500 text-sm">No sources match your filters.</div>
              ) : (
                filteredAndSortedSources.map(source => (
                  <button
                    key={source.source_id}
                    onClick={() => setSelectedSourceId(source.source_id)}
                    className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                      selectedSourceId === source.source_id 
                        ? 'bg-cyan-500/10 border-cyan-500/30 shadow-[0_0_15px_rgba(34,211,238,0.05)]' 
                        : 'bg-zinc-900/40 border-zinc-800/60 hover:bg-zinc-800/40 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${selectedSourceId === source.source_id ? 'bg-cyan-500/20 text-cyan-400' : 'bg-zinc-800 text-zinc-400'}`}>
                           <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                        </div>
                        <div className="truncate">
                          <h4 className={`font-semibold truncate ${selectedSourceId === source.source_id ? 'text-zinc-100' : 'text-zinc-300'}`}>{source.name}</h4>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">{source.detected_format}</span>
                        </div>
                      </div>
                      <div className="flex-shrink-0 ml-2 mt-1">
                        {source.status === 'ready' ? (
                          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" title="Ready"></div>
                        ) : source.status === 'failed' ? (
                          <div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" title="Failed"></div>
                        ) : (
                          <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" title="Processing"></div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-4 mt-3 text-xs text-zinc-400 font-medium px-1">
                      {source.record_count !== undefined && source.record_count > 0 && (
                        <div className="flex items-center gap-1.5">
                           <svg className="w-3.5 h-3.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
                           {source.record_count.toLocaleString()}
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 ml-auto opacity-70">
                        {formatSize(source.size_bytes)}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Right Detail Panel */}
          <div className="flex-1 bg-zinc-900/30 backdrop-blur-md border border-zinc-800/80 rounded-2xl shadow-xl flex flex-col overflow-hidden relative">
             {selectedSource ? (
               <div className="h-full flex flex-col overflow-y-auto custom-scrollbar relative z-10 animate-fade-in">
                 
                 {/* Header Banner */}
                 <div className="h-32 bg-zinc-800/30 border-b border-zinc-800/80 relative flex items-end p-8">
                   <div className="absolute inset-0 bg-gradient-to-r from-cyan-900/10 to-transparent pointer-events-none"></div>
                   <div className="flex items-center gap-5 w-full relative z-10">
                     <div className="w-16 h-16 bg-zinc-900 border border-zinc-700/50 rounded-2xl flex items-center justify-center shadow-lg text-cyan-400">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                     </div>
                     <div className="flex-1 overflow-hidden">
                       <h2 className="text-2xl font-bold text-zinc-100 truncate">{selectedSource.name}</h2>
                       <div className="flex items-center gap-3 mt-1.5 text-sm font-medium">
                         <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${selectedSource.status === 'ready' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : selectedSource.status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                           {selectedSource.status}
                         </span>
                         <span className="text-zinc-400 uppercase text-xs tracking-wider border-l border-zinc-700 pl-3">{selectedSource.detected_format}</span>
                         <span className="text-zinc-500 border-l border-zinc-700 pl-3">Uploaded {new Date(selectedSource.uploaded_at).toLocaleDateString()}</span>
                       </div>
                     </div>
                   </div>
                 </div>

                 {/* Actions */}
                 <div className="p-8 border-b border-zinc-800/50 flex flex-wrap gap-4">
                   <button 
                     onClick={() => navigate('/', { state: { sourceId: selectedSource.source_id } })}
                     disabled={selectedSource.status !== 'ready'}
                     className="bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-semibold px-5 py-2.5 rounded-xl transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                   >
                     <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                     Query Source
                   </button>
                   
                   <button 
                     onClick={() => navigate('/schema', { state: { sourceId: selectedSource.source_id } })}
                     disabled={selectedSource.status !== 'ready'}
                     className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold px-5 py-2.5 rounded-xl transition-colors border border-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                   >
                     <svg className="w-5 h-5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                     View Schema
                   </button>
                   
                   <button 
                     onClick={() => {
                        if (confirm(`Are you sure you want to delete ${selectedSource.name}?`)) {
                           handleDelete(selectedSource.source_id);
                        }
                     }}
                     className="bg-transparent hover:bg-red-500/10 text-zinc-400 hover:text-red-400 font-semibold px-5 py-2.5 rounded-xl transition-colors border border-transparent hover:border-red-500/20 ml-auto flex items-center gap-2"
                   >
                     <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                     Delete
                   </button>
                 </div>

                 {/* Details Content */}
                 <div className="p-8 flex-1">
                   <h3 className="text-lg font-semibold text-zinc-100 mb-4 flex items-center">
                     <svg className="w-5 h-5 mr-2 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                     Source Details
                   </h3>
                   
                   {selectedSource.status === 'failed' && selectedSource.error_message ? (
                      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-5 mb-8 text-red-200/80 text-sm font-mono overflow-auto max-h-40 custom-scrollbar">
                        <strong className="text-red-400 font-sans block mb-2 text-base">Ingestion Error</strong>
                        {selectedSource.error_message}
                      </div>
                   ) : (
                     <div className="grid grid-cols-2 gap-4 mb-8">
                       <div className="bg-zinc-950/40 border border-zinc-800/60 rounded-xl p-5">
                         <div className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-1">Total Records</div>
                         <div className="text-2xl font-bold text-zinc-100">{selectedSource.record_count !== undefined ? selectedSource.record_count.toLocaleString() : '—'}</div>
                       </div>
                       <div className="bg-zinc-950/40 border border-zinc-800/60 rounded-xl p-5">
                         <div className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-1">Tables/Collections</div>
                         <div className="text-2xl font-bold text-zinc-100">{selectedSource.table_count !== undefined ? selectedSource.table_count : '—'}</div>
                       </div>
                       <div className="bg-zinc-950/40 border border-zinc-800/60 rounded-xl p-5">
                         <div className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-1">File Size</div>
                         <div className="text-2xl font-bold text-zinc-100">{formatSize(selectedSource.size_bytes)}</div>
                       </div>
                       <div className="bg-zinc-950/40 border border-zinc-800/60 rounded-xl p-5">
                         <div className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-1">Source ID</div>
                         <div className="text-sm font-mono font-medium text-zinc-400 mt-1 truncate" title={selectedSource.source_id}>{selectedSource.source_id}</div>
                       </div>
                     </div>
                   )}
                   
                   {selectedSource.schema_summary && (
                     <div>
                       <h4 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-3">Schema Summary</h4>
                       <div className="bg-zinc-950/50 border border-zinc-800/50 rounded-xl p-5 text-sm text-zinc-400 leading-relaxed font-mono custom-scrollbar overflow-x-auto whitespace-pre-wrap max-h-60">
                         {typeof selectedSource.schema_summary === 'string' ? selectedSource.schema_summary : JSON.stringify(selectedSource.schema_summary, null, 2)}
                       </div>
                     </div>
                   )}
                 </div>
               </div>
             ) : (
               <div className="h-full flex items-center justify-center text-zinc-500">
                 Select a source to view details
               </div>
             )}
          </div>
        </div>
      )}
    </div>
  );
};
