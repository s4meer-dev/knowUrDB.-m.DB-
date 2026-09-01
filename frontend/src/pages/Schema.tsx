import React, { useEffect, useState } from 'react';
import { getSources, getSourceSchema } from '../services/api';
import type { DatabaseSchema, TableInfo, SourceMetadata } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';

export const Schema: React.FC = () => {
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [summary, setSummary] = useState<DatabaseSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<TableInfo | null>(null);

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
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchSchemaForSource();
  }, [selectedSourceId]);


  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    if (summary) {
      const details = summary.tables.find(t => t.name === tableName);
      setTableDetails(details || null);
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
        <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center text-zinc-500 mb-4">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <p className="text-zinc-400 font-medium text-lg">No relational sources found</p>
        <p className="text-zinc-500 mt-2">Upload a database to view its schema.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-6xl mx-auto animate-fade-in pt-4">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-zinc-100 tracking-tight">Schema Explorer</h2>
          <p className="text-zinc-400 mt-1">
            Explore the structure of your database. {summary?.tables.length || 0} tables available.
          </p>
        </div>
        
        <select 
          value={selectedSourceId || ''} 
          onChange={(e) => setSelectedSourceId(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-zinc-300 focus:outline-none focus:border-cyan-500"
        >
          {sources.map(s => (
            <option key={s.source_id} value={s.source_id}>{s.name}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Table List Sidebar */}
        <div className="w-64 flex flex-col bg-zinc-900/50 backdrop-blur-md rounded-xl shadow-lg border border-zinc-800/80 overflow-hidden">
          <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/80">
            <h3 className="font-semibold text-zinc-300">Tables</h3>
          </div>
          <div className="flex-1 overflow-auto p-2 space-y-1 custom-scrollbar">
            {summary?.tables.map(table => (
              <button
                key={table.name}
                onClick={() => handleTableSelect(table.name)}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-all flex items-center justify-between group
                  ${selectedTable === table.name 
                    ? 'bg-cyan-500/10 text-cyan-400 font-medium border border-cyan-500/20 shadow-[inset_0_0_10px_rgba(34,211,238,0.05)]' 
                    : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200 border border-transparent'}`}
              >
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                  </svg>
                  <span className="truncate">{table.name}</span>
                </div>
                <svg className={`w-4 h-4 opacity-0 transition-opacity ${selectedTable === table.name ? 'opacity-100 text-cyan-500' : 'group-hover:opacity-50'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            ))}
          </div>
        </div>

        {/* Table Details Content */}
        <div className="flex-1 bg-zinc-900/50 backdrop-blur-md rounded-xl shadow-lg border border-zinc-800/80 overflow-hidden flex flex-col">
          {!selectedTable ? (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 p-8 text-center bg-zinc-900/20">
              <svg className="w-16 h-16 mb-4 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
              </svg>
              <p className="text-lg font-medium text-zinc-400">Select a table</p>
              <p className="text-sm mt-1">Choose a table from the list to view its columns and data types.</p>
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
            <>
              <div className="p-6 border-b border-zinc-800/80 flex justify-between items-center bg-zinc-900/80">
                <div>
                  <h3 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                    <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                    </svg>
                    {tableDetails.name}
                  </h3>
                  <p className="text-sm text-zinc-400 mt-1 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                    </svg>
                    {tableDetails.columns.length} columns
                  </p>
                </div>
              </div>
              
              <div className="flex-1 overflow-auto p-0 custom-scrollbar">
                <table className="min-w-full divide-y divide-zinc-800">
                  <thead className="bg-zinc-900/90 sticky top-0 shadow-sm z-10 backdrop-blur-md">
                    <tr>
                      <th scope="col" className="px-6 py-4 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider w-1/3 border-b border-zinc-800/80">
                        Column Name
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider w-1/4 border-b border-zinc-800/80">
                        Data Type
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider border-b border-zinc-800/80">
                        Attributes
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-zinc-900/30 divide-y divide-zinc-800/50">
                    {tableDetails.columns.map((col, idx) => {
                      const isPrimaryKey = tableDetails.primary_keys.includes(col.name) || col.primary_key;
                      const foreignKey = tableDetails.foreign_keys.find(fk => fk.source_column === col.name);
                      
                      return (
                      <tr key={idx} className="hover:bg-zinc-800/40 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-zinc-200">
                          {col.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-cyan-400 font-mono">
                          {col.type || (col as any).data_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500">
                          <div className="flex gap-2">
                            {isPrimaryKey && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                                </svg>
                                Primary Key
                              </span>
                            )}
                            {foreignKey && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                                </svg>
                                FK: {foreignKey.referenced_table}.{foreignKey.referenced_column}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )})}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
