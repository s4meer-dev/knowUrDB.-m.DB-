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
    <div className="bg-[#09090b]/80 backdrop-blur-xl rounded-2xl shadow-xl border border-zinc-800/80 overflow-hidden flex flex-col mt-4 max-h-[800px] animate-fade-in relative">
      <div className="absolute inset-0 bg-gradient-to-b from-zinc-800/20 to-transparent pointer-events-none"></div>
      
      {/* Result Header */}
      <div className="bg-zinc-900/90 border-b border-zinc-800/80 px-6 py-4 flex flex-wrap items-center justify-between gap-4 relative z-10">
        <div>
          <h2 className="font-semibold text-zinc-100 flex items-center tracking-tight">
            {isLoading && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-cyan-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {isLoading ? 'Analyzing...' : 'Result'}
          </h2>
          <p className="text-sm text-zinc-400 mt-0.5 line-clamp-1 font-medium" title={result.question}>
            {result.question}
          </p>
        </div>
        
        {result.generated_sql && result.status === 'success' && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          >
            <svg className={`w-3.5 h-3.5 mr-1.5 transition-transform ${showSql ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
            </svg>
            {showSql ? 'Hide SQL' : 'View SQL'}
          </button>
        )}
      </div>

      <div className={`transition-opacity duration-300 flex flex-col overflow-hidden relative z-10 ${isLoading ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
        {/* SQL Panel */}
        {showSql && result.generated_sql && result.status === 'success' && (
          <SqlPanel sql={result.generated_sql} />
        )}

        {/* Explanation */}
        {result.status === 'success' && (
          <ExplanationPanel explanation={result.explanation} />
        )}

        {/* Body */}
        <div className="flex-grow overflow-auto relative min-h-[150px]">
          {result.status === 'error' ? (
            <div className="p-8">
              <ErrorState 
                title="I couldn't answer that" 
                message={result.error || 'Please try rephrasing your question or checking the schema.'} 
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
