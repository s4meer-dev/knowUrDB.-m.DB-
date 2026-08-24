import React, { useState } from 'react';
import type { QueryResponse } from '../../types';
import { ResultsTable } from './ResultsTable';
import { SqlPanel } from './SqlPanel';
import { ExplanationPanel } from './ExplanationPanel';
import { MetadataPanel } from './MetadataPanel';
import { FollowUpSuggestions } from './FollowUpSuggestions';
import { ErrorState } from '../common/ErrorState';

interface QueryResultProps {
  result: QueryResponse | null;
  isLoading: boolean;
  onFollowUp: (question: string) => void;
}

export const QueryResult: React.FC<QueryResultProps> = ({ result, isLoading, onFollowUp }) => {
  const [showSql, setShowSql] = useState<boolean>(false);

  if (!result && !isLoading) {
    return null; // Handled by empty state in Workspace
  }

  if (isLoading && !result) {
    // Initial loading state (no previous result)
    return null;
  }

  if (!result) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col mt-6 max-h-[800px]">
      {/* Result Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-semibold text-gray-800 flex items-center">
            {isLoading && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            Query Result
          </h2>
          <p className="text-sm text-gray-500 mt-1 line-clamp-1" title={result.question}>
            "{result.question}"
          </p>
        </div>
        
        {result.generated_sql && result.status === 'success' && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors"
          >
            <svg className={`w-4 h-4 mr-1.5 transition-transform ${showSql ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
            </svg>
            {showSql ? 'Hide SQL' : 'View SQL'}
          </button>
        )}
      </div>

      <div className={`transition-opacity duration-200 flex flex-col overflow-hidden ${isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
        {/* SQL Panel */}
        {showSql && result.generated_sql && result.status === 'success' && (
          <SqlPanel sql={result.generated_sql} />
        )}

        {/* Explanation */}
        {result.status === 'success' && (
          <ExplanationPanel explanation={result.explanation} />
        )}

        {/* Body */}
        <div className="flex-grow overflow-auto relative">
          {result.status === 'error' ? (
            <div className="p-6">
              <ErrorState 
                title="Query Failed" 
                message={result.error || 'An unexpected error occurred'} 
              />
            </div>
          ) : (
            <ResultsTable columns={result.columns} rows={result.rows} />
          )}
        </div>

        {/* Follow-ups */}
        {result.status === 'success' && (
          <FollowUpSuggestions 
            suggestions={result.follow_up_suggestions} 
            onSelect={onFollowUp} 
            disabled={isLoading}
          />
        )}

        {/* Metadata */}
        {result.status === 'success' && (
          <MetadataPanel 
            rowCount={result.row_count} 
            executionTimeMs={result.execution_time_ms} 
            querySource={result.query_source}
          />
        )}
      </div>
    </div>
  );
};
