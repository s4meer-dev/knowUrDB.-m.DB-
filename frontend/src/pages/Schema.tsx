import React, { useEffect, useState } from 'react';
import { getSources, getSourceSchema, getSourceTableSample } from '../services/api';
import type { DatabaseSchema, TableInfo, SourceMetadata } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';
import { ResultsTable } from '../components/workspace/ResultsTable';
import { CustomDropdown } from '../components/common/CustomDropdown';

export const Schema: React.FC = () => {
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [summary, setSummary] = useState<DatabaseSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<TableInfo | null>(null);
  
  const [activeTab, setActiveTab] = useState<'schema' | 'data'>('schema');
  
  const [sampleData, setSampleData] = useState<{ columns: string[], rows: any[] } | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        const data = await getSources();
        const relationalSources = data.filter(s => s.detected_format !== 'pdf' && s.detected_format !== 'txt' && s.detected_format !== 'markdown');
        setSources(relationalSources);
        if (relationalSources.length > 0) {
          setSelectedSourceId(relationalSources[0].source_id);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  useEffect(() => {
    const fetchSchemaForSource = async () => {
      if (!selectedSourceId) return;
      try {
        setLoading(true);
        const data = await getSourceSchema(selectedSourceId);
        setSummary(data);
        setSelectedTable(null);
        setTableDetails(null);
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
      setSampleError(e?.response?.data?.detail || e.message || 'Failed to load sample data.');
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

  const handleTabChange = (tab: 'schema' | 'data') => {
    setActiveTab(tab);
    if (tab === 'data' && !sampleData && !loadingSample && selectedTable) {
      fetchSampleData(selectedTable);
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <ErrorState 
          title="Failed to load schema" 
          message="Could not retrieve database schema information."
        />
      </div>
    );
  }

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner text="Analyzing database schema..." size="lg" />
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-full flex-col text-center">
        <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center text-zinc-500 mb-4 border border-zinc-700/50 shadow-lg">
          <svg className="w-8 h-8 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <p className="text-zinc-100 font-bold text-xl tracking-tight mb-2">No structured databases found</p>
        <p className="text-zinc-400 max-w-sm">Upload a database (SQLite, DuckDB, CSV) in the Knowledge Base to view and explore its schema.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-7xl mx-auto animate-fade-in pt-4 pb-4">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-zinc-100 tracking-tight">Schema Explorer</h2>
          <p className="text-zinc-400 mt-1.5">
            Explore {summary?.tables.length || 0} tables and preview live data from your connected sources.
          </p>
        </div>
        
        <div className="relative mt-2">
          <label className="absolute -top-2.5 left-3 px-1 bg-[#09090b] text-[10px] font-bold uppercase tracking-wider text-cyan-500 z-10">Active Source</label>
          <CustomDropdown 
            value={selectedSourceId || ''} 
            onChange={(val) => setSelectedSourceId(val)}
            options={sources.map(s => ({ value: s.source_id, label: s.name }))}
            triggerClassName="bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 font-medium hover:bg-zinc-800/50 transition-colors min-w-[250px]"
          />
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Table List Sidebar */}
        <div className="w-[300px] flex flex-col bg-zinc-900/40 backdrop-blur-xl rounded-2xl shadow-xl border border-zinc-800/80 overflow-hidden flex-shrink-0">
          <div className="p-5 border-b border-zinc-800/80 bg-gradient-to-r from-zinc-800/30 to-transparent flex items-center justify-between">
            <h3 className="font-bold text-zinc-100 tracking-tight flex items-center gap-2">
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
              Tables
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
                <div className="flex items-center overflow-hidden">
                  <svg className={`w-4 h-4 mr-2.5 flex-shrink-0 ${selectedTable === table.name ? 'text-cyan-400 opacity-100' : 'text-zinc-500 opacity-70 group-hover:text-zinc-400 group-hover:opacity-100'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                  <span className="truncate">{table.name}</span>
                </div>
                <svg className={`w-4 h-4 flex-shrink-0 opacity-0 transition-opacity ${selectedTable === table.name ? 'opacity-100 text-cyan-500' : 'group-hover:opacity-50'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            ))}
          </div>
        </div>

        {/* Table Details Content */}
        <div className="flex-1 bg-zinc-900/40 backdrop-blur-xl rounded-2xl shadow-xl border border-zinc-800/80 overflow-hidden flex flex-col relative">
          {!selectedTable ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-zinc-800/5 to-zinc-900/20 relative z-10 animate-fade-in">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/10 via-zinc-900/0 to-zinc-900/0 pointer-events-none"></div>
              <div className="w-20 h-20 bg-zinc-900 rounded-2xl border border-zinc-700/50 flex items-center justify-center text-zinc-500 mb-6 shadow-2xl relative z-10">
                <svg className="w-10 h-10 text-cyan-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
                </svg>
              </div>
              <p className="text-xl font-bold text-zinc-100 tracking-tight mb-2 relative z-10">Select a table to explore</p>
              <p className="text-zinc-400 relative z-10 max-w-sm">Choose a table from the sidebar to view its column definitions, relationships, and sample data.</p>
            </div>
          ) : !tableDetails ? (
            <div className="flex-1 flex items-center justify-center p-8">
              <ErrorState 
                title="Table not found" 
                message={`Could not load schema for ${selectedTable}.`}
                onRetry={() => handleTableSelect(selectedTable)}
              />
            </div>
          ) : (
            <div className="flex flex-col h-full animate-fade-in">
              <div className="pt-6 px-6 pb-0 border-b border-zinc-800/80 bg-zinc-800/20 relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-900/10 to-transparent pointer-events-none"></div>
                <div className="relative z-10 flex justify-between items-end mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-zinc-100 flex items-center gap-3 tracking-tight">
                      {tableDetails.name}
                    </h3>
                    <p className="text-sm font-medium text-zinc-400 mt-2 flex items-center gap-4">
                      <span className="flex items-center">
                         <svg className="w-4 h-4 mr-1.5 opacity-70 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
                         {tableDetails.columns.length} columns
                      </span>
                      {tableDetails.primary_keys.length > 0 && (
                        <span className="flex items-center text-amber-400/80">
                           <svg className="w-4 h-4 mr-1.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
                           PK: {tableDetails.primary_keys.join(', ')}
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex gap-6 relative z-10">
                   <button 
                     onClick={() => handleTabChange('schema')}
                     className={`pb-3 text-sm font-semibold transition-all border-b-2 ${activeTab === 'schema' ? 'text-cyan-400 border-cyan-400' : 'text-zinc-400 border-transparent hover:text-zinc-200 hover:border-zinc-700'}`}
                   >
                     Schema Definition
                   </button>
                   <button 
                     onClick={() => handleTabChange('data')}
                     className={`pb-3 text-sm font-semibold transition-all border-b-2 ${activeTab === 'data' ? 'text-cyan-400 border-cyan-400' : 'text-zinc-400 border-transparent hover:text-zinc-200 hover:border-zinc-700'}`}
                   >
                     Data Sample (50 rows)
                   </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-hidden bg-zinc-900/10">
                {activeTab === 'schema' ? (
                  <div className="h-full overflow-auto custom-scrollbar">
                    <table className="min-w-full divide-y divide-zinc-800/80">
                      <thead className="bg-zinc-900/90 sticky top-0 shadow-sm z-10 backdrop-blur-xl">
                        <tr>
                          <th scope="col" className="px-8 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider w-[40%] border-b border-zinc-800">
                            Column Name
                          </th>
                          <th scope="col" className="px-8 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider w-[25%] border-b border-zinc-800">
                            Data Type
                          </th>
                          <th scope="col" className="px-8 py-4 text-left text-xs font-bold text-zinc-400 uppercase tracking-wider border-b border-zinc-800">
                            Attributes & Relations
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/40 bg-transparent">
                        {tableDetails.columns.map((col, idx) => {
                          const isPrimaryKey = tableDetails.primary_keys.includes(col.name) || col.primary_key;
                          const foreignKey = tableDetails.foreign_keys.find(fk => fk.source_column === col.name);
                          
                          return (
                          <tr key={idx} className="hover:bg-zinc-800/30 transition-colors group">
                            <td className="px-8 py-4 whitespace-nowrap text-sm font-bold text-zinc-200 group-hover:text-white transition-colors">
                              {col.name}
                            </td>
                            <td className="px-8 py-4 whitespace-nowrap text-sm text-cyan-400/90 font-mono font-medium">
                              {col.type || (col as any).data_type}
                            </td>
                            <td className="px-8 py-4 whitespace-nowrap text-sm text-zinc-400">
                              <div className="flex flex-wrap gap-2">
                                {isPrimaryKey && (
                                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm">
                                    <svg className="w-3.5 h-3.5 mr-1.5 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                                    </svg>
                                    Primary Key
                                  </span>
                                )}
                                {foreignKey && (
                                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm">
                                    <svg className="w-3.5 h-3.5 mr-1.5 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                                    </svg>
                                    FK &rarr; {foreignKey.referenced_table}.{foreignKey.referenced_column}
                                  </span>
                                )}
                                {!isPrimaryKey && !foreignKey && (
                                  <span className="text-zinc-600 italic text-xs">&mdash;</span>
                                )}
                              </div>
                            </td>
                          </tr>
                        )})}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="h-full flex flex-col relative">
                     {loadingSample ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-zinc-900/20">
                          <LoadingSpinner text={`Fetching sample data for ${tableDetails.name}...`} size="md" />
                        </div>
                     ) : sampleError ? (
                        <div className="flex-1 flex items-center justify-center p-8 bg-zinc-900/20">
                          <ErrorState 
                            title="Cannot fetch sample data" 
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
                           <svg className="w-12 h-12 mb-3 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                           <p className="font-medium text-zinc-400">No data found in this table.</p>
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
