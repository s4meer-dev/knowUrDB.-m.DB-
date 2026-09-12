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
  onFollowUp: (question: string, sourceIds?: string[]) => void;
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
          {result.status === 'clarification_required' ? (
            <div className="p-8">
              <div className="flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                </div>
                <h3 className="text-xl font-bold text-zinc-100 mb-2">Clarification Required</h3>
                <p className="text-zinc-400 mb-6">{result.error}</p>
                <div className="flex flex-col w-full max-w-md gap-3">
                  {result.candidates?.map(c => (
                    <button 
                      key={c.source_id}
                      onClick={() => onFollowUp(result.question, [c.source_id])}
                      className="bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700/50 p-4 rounded-xl text-left transition-colors flex items-center justify-between group"
                    >
                      <span className="font-medium text-zinc-200">{c.name}</span>
                      <svg className="w-4 h-4 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : result.status === 'error' ? (
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

        {/* Sources Citation */}
        {result.status === 'success' && result.sources && result.sources.length > 0 && (
          <div className="bg-[#09090b] border-t border-zinc-800/80 p-3 px-6 text-xs text-zinc-400">
            <span className="font-semibold text-zinc-300">Sources: </span>
            {result.sources.map((s, idx) => (
              <span key={s.source_id}>
                {s.name}
                {s.table && <span className="text-zinc-500"> ({s.table})</span>}
                {s.page && <span className="text-zinc-500"> (Page {s.page})</span>}
                {idx < (result.sources?.length || 0) - 1 ? ', ' : ''}
              </span>
            ))}
          </div>
        )}

        {/* Metadata */}
        {result.status === 'success' && (
          <MetadataPanel 
            rowCount={result.row_count} 
            executionTimeMs={result.execution_time_ms} 
            querySource={result.query_source}
            confidence={result.confidence}
          />
        )}
      </div>
    </div>
  );
};
