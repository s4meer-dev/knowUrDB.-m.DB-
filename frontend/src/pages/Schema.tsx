import React, { useEffect, useState } from 'react';
import { getSchema } from '../services/api';
import type { DatabaseSchema, TableInfo } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorState } from '../components/common/ErrorState';

export const Schema: React.FC = () => {
  const [summary, setSummary] = useState<DatabaseSchema | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [errorSummary, setErrorSummary] = useState(false);

  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<TableInfo | null>(null);

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      setErrorSummary(false);
      const data = await getSchema();
      setSummary(data);
    } catch {
      setErrorSummary(true);
    } finally {
      setLoadingSummary(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    if (summary) {
      const details = summary.tables.find(t => t.name === tableName);
      setTableDetails(details || null);
    }
  };

  if (errorSummary) {
    return (
      <div className="flex items-center justify-center h-full">
        <ErrorState 
          title="Failed to load schema" 
          message="Could not retrieve database schema information."
          onRetry={fetchSummary}
        />
      </div>
    );
  }

  if (loadingSummary) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner text="Analyzing database schema..." size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 tracking-tight">Schema Explorer</h2>
        <p className="text-gray-500 mt-1">
          Explore the structure of your database. {summary?.tables.length} tables available.
        </p>
      </div>

      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Table List Sidebar */}
        <div className="w-64 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="font-semibold text-gray-700">Tables</h3>
          </div>
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {summary?.tables.map(table => (
              <button
                key={table.name}
                onClick={() => handleTableSelect(table.name)}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-colors flex items-center justify-between group
                  ${selectedTable === table.name 
                    ? 'bg-indigo-50 text-indigo-700 font-medium' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}
              >
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                  </svg>
                  <span className="truncate">{table.name}</span>
                </div>
                <svg className={`w-4 h-4 opacity-0 transition-opacity ${selectedTable === table.name ? 'opacity-100 text-indigo-500' : 'group-hover:opacity-50'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
            ))}
          </div>
        </div>

        {/* Table Details Content */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          {!selectedTable ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 p-8 text-center bg-gray-50">
              <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
              </svg>
              <p className="text-lg font-medium text-gray-600">Select a table</p>
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
              <div className="p-6 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                <div>
                  <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                    </svg>
                    {tableDetails.name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                    </svg>
                    {tableDetails.columns.length} columns
                  </p>
                </div>
              </div>
              
              <div className="flex-1 overflow-auto p-0">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0 shadow-sm z-10">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/3">
                        Column Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/4">
                        Data Type
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Attributes
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {tableDetails.columns.map((col, idx) => {
                      const isPrimaryKey = tableDetails.primary_keys.includes(col.name) || col.primary_key;
                      const foreignKey = tableDetails.foreign_keys.find(fk => fk.source_column === col.name);
                      
                      return (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {col.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-indigo-600 font-mono">
                          {col.type || (col as any).data_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex gap-2">
                            {isPrimaryKey && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
                                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                                </svg>
                                Primary Key
                              </span>
                            )}
                            {foreignKey && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
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
