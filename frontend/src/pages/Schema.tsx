import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { getSources, getSourceSchema, getSourceTableSample, activateSource } from '../services/api';
import type { DatabaseSchema, TableInfo, SourceMetadata } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { ResultsTable } from '../components/workspace/ResultsTable';
import { CustomDropdown } from '../components/common/CustomDropdown';

export const Schema: React.FC = () => {
  const location = useLocation();
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(() => {
    const stateSourceId = (location.state as { sourceId?: string } | null)?.sourceId;
    return stateSourceId || localStorage.getItem('knowurdb_active_source_id');
  });
  const [summary, setSummary] = useState<DatabaseSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<TableInfo | null>(null);
  
  const [activeTab, setActiveTab] = useState<'schema' | 'indexes' | 'data'>('schema');
  
  const [sampleData, setSampleData] = useState<{ columns: string[], rows: any[] } | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        const data = await getSources();
        setSources(data);
        const stateSourceId = (location.state as { sourceId?: string } | null)?.sourceId;
        const savedSourceId = localStorage.getItem('knowurdb_active_source_id');
        const preferred = stateSourceId || savedSourceId;
        if (preferred && data.some((s) => s.source_id === preferred)) {
          setSelectedSourceId(preferred);
          localStorage.setItem('knowurdb_active_source_id', preferred);
        } else if (data.length > 0) {
          setSelectedSourceId(data[0].source_id);
          localStorage.setItem('knowurdb_active_source_id', data[0].source_id);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, [location.state]);

  useEffect(() => {
    const fetchSchemaForSource = async () => {
      if (!selectedSourceId) return;
      try {
        setLoading(true);
        localStorage.setItem('knowurdb_active_source_id', selectedSourceId);
        activateSource(selectedSourceId).catch(() => {});
        const data = await getSourceSchema(selectedSourceId);
        setSummary(data);
        if (data.tables && data.tables.length > 0) {
          setSelectedTable(data.tables[0].name);
          setTableDetails(data.tables[0]);
        } else {
          setSelectedTable(null);
          setTableDetails(null);
        }
        setSampleData(null);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchSchemaForSource();
  }, [selectedSourceId]);

  const fetchSampleData = async (tableName: string) => {
    if (!selectedSourceId) return;
    try {
      setLoadingSample(true);
      setSampleError(null);
      const data = await getSourceTableSample(selectedSourceId, tableName, 50);
      setSampleData(data);
    } catch (e: any) {
      setSampleError(e?.response?.data?.detail || e.message || 'Failed to load sample documents.');
      setSampleData(null);
    } finally {
      setLoadingSample(false);
    }
  };

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    setActiveTab('schema');
    setSampleData(null);
    setSampleError(null);
    if (summary) {
      const details = summary.tables.find(t => t.name === tableName);
      setTableDetails(details || null);
    }
  };

  const handleTabChange = (tab: 'schema' | 'indexes' | 'data') => {
    setActiveTab(tab);
    if (tab === 'data' && !sampleData && !loadingSample && selectedTable) {
      fetchSampleData(selectedTable);
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <ErrorState 
          title="Failed to load MongoDB schema" 
          message="Could not retrieve collection and document schema metadata."
        />
      </div>
    );
  }

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner text="Introspecting MongoDB collections & BSON types..." size="lg" />
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-full flex-col text-center">
        <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center text-zinc-500 mb-4 border border-zinc-700/50 shadow-lg">
          <svg className="w-8 h-8 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <p className="text-zinc-100 font-bold text-xl tracking-tight mb-2">No MongoDB collections found</p>
        <p className="text-zinc-400 max-w-sm">Upload a dataset or generate the Demo Database in the Knowledge Base to explore collections and nested BSON fields.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-7xl mx-auto animate-fade-in pt-4 pb-4">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-zinc-100 tracking-tight">MongoDB Schema Explorer</h2>
          <p className="text-zinc-400 mt-1.5">
            Inspect {summary?.tables.length || 0} collections, BSON field types, nested subdocuments, indexes, and sample documents.
          </p>
        </div>
        
        <div className="relative mt-2">
          <label className="absolute -top-2.5 left-3 px-1 bg-[#09090b] text-[10px] font-bold uppercase tracking-wider text-cyan-500 z-10">Active Source</label>
          <CustomDropdown 
            value={selectedSourceId || ''} 
            onChange={(val) => setSelectedSourceId(val)}
            options={sources.map(s => ({ value: s.source_id, label: s.name }))}
            triggerClassName="bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 font-medium hover:bg-zinc-800/50 transition-colors min-w-[260px]"
          />
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Collection List Sidebar */}
        <div className="w-[300px] flex flex-col bg-zinc-900/40 backdrop-blur-xl rounded-2xl shadow-xl border border-zinc-800/80 overflow-hidden flex-shrink-0">
          <div className="p-5 border-b border-zinc-800/80 bg-gradient-to-r from-zinc-800/30 to-transparent flex items-center justify-between">
            <h3 className="font-bold text-zinc-100 tracking-tight flex items-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
              Collections
            </h3>
            <span className="text-xs font-semibold bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full">{summary?.tables.length || 0}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
            {summary?.tables.map(table => (
              <button
                key={table.name}
                onClick={() => handleTableSelect(table.name)}
                className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all duration-200 flex items-center justify-between group
                  ${selectedTable === table.name 
                    ? 'bg-cyan-500/10 text-cyan-400 font-semibold border border-cyan-500/20 shadow-[0_0_15px_rgba(34,211,238,0.05)]' 
                    : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200 border border-transparent'}`}
              >
                <div className="flex flex-col overflow-hidden">
                  <span className="truncate font-mono">{table.name}</span>
                  {table.document_count !== undefined && (
                    <span className="text-[11px] text-zinc-500 font-normal">
                      {table.document_count.toLocaleString()} docs • {table.columns.length} fields
                    </span>
                  )}
                </div>
                <svg className={`w-4 h-4 flex-shrink-0 opacity-0 transition-opacity ${selectedTable === table.name ? 'opacity-100 text-cyan-500' : 'group-hover:opacity-50'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            ))}
          </div>
        </div>

        {/* Collection Details Content */}
        <div className="flex-1 bg-zinc-900/40 backdrop-blur-xl rounded-2xl shadow-xl border border-zinc-800/80 overflow-hidden flex flex-col relative">
          {!selectedTable || !tableDetails ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <p className="text-xl font-bold text-zinc-100 tracking-tight mb-2">Select a MongoDB collection</p>
              <p className="text-zinc-400 max-w-sm">Choose a collection from the sidebar to inspect its BSON document structure, indexes, and sample documents.</p>
            </div>
          ) : (
            <div className="flex flex-col h-full animate-fade-in">
              <div className="pt-6 px-6 pb-0 border-b border-zinc-800/80 bg-zinc-800/20 relative">
                <div className="relative z-10 flex justify-between items-end mb-6">
                  <div>
                    <h3 className="text-2xl font-bold font-mono text-zinc-100 flex items-center gap-3 tracking-tight">
                      db.{tableDetails.name}
                    </h3>
                    <p className="text-sm font-medium text-zinc-400 mt-2 flex items-center gap-4">
                      <span className="text-emerald-400/90">
                        {(tableDetails.document_count || 0).toLocaleString()} documents
                      </span>
                      <span>•</span>
                      <span>{tableDetails.columns.length} inferred BSON paths</span>
                      {tableDetails.indexes && (
                        <>
                          <span>•</span>
                          <span className="text-cyan-400/90">{tableDetails.indexes.length} indexes</span>
                        </>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex gap-6 relative z-10">
                   <button 
                     onClick={() => handleTabChange('schema')}
                     className={`pb-3 text-sm font-semibold transition-all border-b-2 ${activeTab === 'schema' ? 'text-cyan-400 border-cyan-400' : 'text-zinc-400 border-transparent hover:text-zinc-200'}`}
                   >
                     Document Fields & BSON Types
                   </button>
                   <button 
                     onClick={() => handleTabChange('indexes')}
                     className={`pb-3 text-sm font-semibold transition-all border-b-2 ${activeTab === 'indexes' ? 'text-cyan-400 border-cyan-400' : 'text-zinc-400 border-transparent hover:text-zinc-200'}`}
                   >
                     Indexes & Sample BSON ({tableDetails.indexes?.length || 1})
                   </button>
                   <button 
                     onClick={() => handleTabChange('data')}
                     className={`pb-3 text-sm font-semibold transition-all border-b-2 ${activeTab === 'data' ? 'text-cyan-400 border-cyan-400' : 'text-zinc-400 border-transparent hover:text-zinc-200'}`}
                   >
                     Document Preview (50 docs)
                   </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-hidden bg-zinc-900/10">
                {activeTab === 'schema' ? (
                  <div className="h-full overflow-auto custom-scrollbar">
                    <table className="min-w-full divide-y divide-zinc-800/80">
                      <thead className="bg-zinc-900/90 sticky top-0 shadow-sm z-10 backdrop-blur-xl">
                        <tr>
                          <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider w-[35%] border-b border-zinc-800">
                            Field Path
                          </th>
                          <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider w-[20%] border-b border-zinc-800">
                            BSON Type
                          </th>
                          <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider border-b border-zinc-800">
                            Structure, $lookup Relations & Sample Values
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/40 bg-transparent">
                        {tableDetails.columns.map((col, idx) => {
                          const isPrimaryKey = tableDetails.primary_keys.includes(col.name) || col.primary_key;
                          const foreignKey = tableDetails.foreign_keys.find(fk => fk.source_column === col.name);
                          
                          return (
                          <tr key={idx} className="hover:bg-zinc-800/30 transition-colors group">
                            <td className="px-6 py-3.5 whitespace-nowrap text-sm font-mono font-semibold text-zinc-200">
                              {col.name}
                            </td>
                            <td className="px-6 py-3.5 whitespace-nowrap text-xs text-cyan-400 font-mono font-bold">
                              <span className="px-2 py-1 rounded bg-cyan-500/10 border border-cyan-500/20">
                                {col.data_type || col.type}
                              </span>
                            </td>
                            <td className="px-6 py-3.5 text-sm text-zinc-400">
                              <div className="flex flex-wrap items-center gap-2">
                                {isPrimaryKey && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                    Indexed Key
                                  </span>
                                )}
                                {col.is_nested && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                    Embedded Path
                                  </span>
                                )}
                                {col.is_array && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                    Array []
                                  </span>
                                )}
                                {foreignKey && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                    $lookup &rarr; {foreignKey.referenced_table}.{foreignKey.referenced_column}
                                  </span>
                                )}
                                {col.sample_values && col.sample_values.length > 0 && (
                                  <span className="text-xs font-mono text-zinc-500 truncate max-w-xs">
                                    e.g. {col.sample_values.slice(0, 2).map(v => JSON.stringify(v)).join(', ')}
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        )})}
                      </tbody>
                    </table>
                  </div>
                ) : activeTab === 'indexes' ? (
                  <div className="h-full overflow-auto custom-scrollbar p-6 space-y-6">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">Active MongoDB Indexes</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {(tableDetails.indexes || []).map((idx, i) => (
                          <div key={i} className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                            <div>
                              <div className="font-mono text-sm font-bold text-zinc-200">{idx.name}</div>
                              <div className="text-xs font-mono text-cyan-400 mt-1">Keys: {idx.keys.join(', ')}</div>
                            </div>
                            {idx.unique && (
                              <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                Unique
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {tableDetails.sample_document && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">Sample Native BSON Document</h4>
                        <pre className="bg-zinc-950/80 border border-zinc-800/80 rounded-xl p-5 text-xs font-mono text-emerald-300/90 overflow-x-auto leading-relaxed">
                          {JSON.stringify(tableDetails.sample_document, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex flex-col relative">
                     {loadingSample ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-zinc-900/20">
                          <LoadingSpinner text={`Fetching sample documents from ${tableDetails.name}...`} size="md" />
                        </div>
                     ) : sampleError ? (
                        <div className="flex-1 flex items-center justify-center p-8 bg-zinc-900/20">
                          <ErrorState 
                            title="Cannot fetch sample documents" 
                            message={sampleError}
                            onRetry={() => fetchSampleData(tableDetails.name)}
                          />
                        </div>
                     ) : sampleData && sampleData.rows.length > 0 ? (
                        <div className="flex-1 overflow-auto custom-scrollbar">
                           <ResultsTable columns={sampleData.columns} rows={sampleData.rows} />
                        </div>
                     ) : (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 text-zinc-500 bg-zinc-900/20">
                           <p className="font-medium text-zinc-400">No documents found in this collection.</p>
                        </div>
                     )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
