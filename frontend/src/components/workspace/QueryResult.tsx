import React, { useState } from 'react';
import type { QueryResponse } from '../../types';
import { ResultsTable } from './ResultsTable';
import { SqlPanel } from './SqlPanel';
import { FollowUpSuggestions } from './FollowUpSuggestions';
import { ErrorState } from '../common/ErrorState';
import { VisualizationEngine } from './VisualizationEngine';


interface QueryResultProps {
  result: QueryResponse | null;
  isLoading: boolean;
  onFollowUp: (question: string, sourceIds?: string[]) => void;
}

export const QueryResult: React.FC<QueryResultProps> = ({ result, isLoading, onFollowUp }) => {
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);

  if (!result && !isLoading) {
    return null;
  }

  if (isLoading && !result) {
    return null;
  }

  if (!result) return null;

  return (
    <div className="bg-[#09090b]/90 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.8)] border border-zinc-800/80 flex flex-col mt-6 animate-in slide-in-from-bottom-4 fade-in duration-700 ease-out relative overflow-hidden ring-1 ring-white/5">
      <div className="absolute inset-0 bg-gradient-to-b from-cyan-900/5 to-transparent pointer-events-none"></div>
      
      {/* 1. Result Header */}
      <div className="bg-zinc-900/40 border-b border-zinc-800/60 px-6 py-4 flex flex-wrap items-center justify-between gap-4 relative z-10">
        <div>
          <h2 className="font-semibold text-zinc-100 flex items-center tracking-tight text-[15px]">
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing Database...
              </>
            ) : (
              <>
                <div className="relative flex h-2 w-2 mr-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]"></span>
                </div>
                Analysis Complete
              </>
            )}
          </h2>
        </div>
      </div>

      <div className={`transition-opacity duration-300 flex flex-col p-6 overflow-hidden relative z-10 ${isLoading ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
        
        {/* Error / Clarification State */}
        {result.status === 'clarification_required' ? (
          <div className="flex flex-col items-center justify-center text-center py-8">
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
        ) : result.status === 'error' ? (
          result.error_code === 'UNRELATED_QUERY' ? (
            <div className="flex flex-col items-center justify-center text-center py-10 px-4">
              <div className="w-16 h-16 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center mb-6 shadow-inner">
                <svg className="w-8 h-8 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-zinc-200 mb-2 tracking-tight">Unrelated Question</h3>
              <p className="text-zinc-400 max-w-md leading-relaxed">{result.error}</p>
            </div>
          ) : result.error_code === 'SOURCE_NOT_FOUND' ? (
             <div className="flex flex-col items-center justify-center text-center py-10 px-4">
              <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6 shadow-inner">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-zinc-200 mb-2 tracking-tight">Source Not Found</h3>
              <p className="text-zinc-400 max-w-md leading-relaxed">{result.error}</p>
            </div>
          ) : (
            <ErrorState 
              title={result.error_code === 'UNSAFE_SQL' ? "Safety Violation" : result.error_code === 'AI_GENERATION_FAILED' ? "AI Analysis Error" : "Query Error"} 
              message={result.error || 'Please try rephrasing your question or checking the schema.'}
              type="error"
            />
          )
        ) : (
          <>
            {/* 2. Primary Answer */}
            {result.answer && (
              <div className="mb-8 relative">
                {result.answer.headline && (
                  <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-widest mb-3 flex items-center drop-shadow-[0_0_8px_rgba(34,211,238,0.4)]">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    {result.answer.headline}
                  </div>
                )}
                <div className="flex items-baseline flex-wrap gap-x-3 gap-y-1 min-w-0">
                  {result.answer.value && (
                    <h3 className="text-4xl sm:text-5xl font-light text-white tracking-tight drop-shadow-[0_0_15px_rgba(34,211,238,0.2)] break-words break-all">
                      {result.answer.value}
                    </h3>
                  )}
                  {result.answer.unit && (
                    <span className="text-xl sm:text-2xl text-zinc-400 font-light tracking-wide shrink-0">
                      {result.answer.unit}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* 3. Key Insights / Summary */}
            {(result.answer?.summary || (result.insights && result.insights.length > 0)) && (
              <div className="mb-8 bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-5 shadow-inner">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                  Key Insight
                </h4>
                {result.answer?.summary && (
                  <p className="text-zinc-200 text-[15px] leading-relaxed">
                    {result.answer.summary}
                  </p>
                )}
                {result.insights && result.insights.length > 0 && (
                  <ul className="space-y-2 mt-3 text-[14px] text-zinc-400">
                    {result.insights.map((insight, i) => (
                      <li key={i} className="flex items-start">
                        <span className="text-cyan-500 mr-2 mt-1 flex-shrink-0 leading-none">•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* 4. Visualization Engine */}
            {result.columns && result.columns.length > 0 && result.rows && (
              <VisualizationEngine columns={result.columns} rows={result.rows} />
            )}

            {/* 5. Data Table */}
            {result.columns && result.columns.length > 0 && result.rows && result.rows.length > 0 && (
              <div className="mb-8">
                 <ResultsTable columns={result.columns} rows={result.rows} />
              </div>
            )}

            {/* Follow-ups */}
            <FollowUpSuggestions 
              suggestions={result.follow_up_suggestions} 
              onSelect={onFollowUp} 
              disabled={isLoading}
            />

            {/* 6. Technical Details (Collapsible) */}
            <div className="mt-8 border-t border-white/5 pt-6">
              <button 
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="flex items-center text-xs font-semibold text-zinc-500 hover:text-cyan-400 uppercase tracking-widest transition-colors mb-4 focus:outline-none"
              >
                <svg className={`w-4 h-4 mr-2 transition-transform duration-300 ${showTechDetails ? 'rotate-90 text-cyan-400' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                Technical Details
              </button>
              
              <div className={`transition-all duration-500 overflow-hidden ${showTechDetails ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="space-y-4">
                  
                  {/* Execution Metadata */}
                  <div className="flex flex-wrap gap-4">
                    <div className="bg-black/30 border border-white/5 rounded-lg px-4 py-3 flex flex-col min-w-[120px]">
                       <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">Execution Time</span>
                       <span className="text-zinc-300 font-mono text-sm">{result.execution_time_ms} ms</span>
                    </div>
                    <div className="bg-black/30 border border-white/5 rounded-lg px-4 py-3 flex flex-col min-w-[120px]">
                       <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider mb-1">Rows Returned</span>
                       <span className="text-zinc-300 font-mono text-sm">{result.row_count}</span>
                    </div>
                  </div>

                  {/* Sources Citation */}
                  {result.sources && result.sources.length > 0 && (
                    <div className="bg-black/30 border border-white/5 p-4 rounded-xl text-xs text-zinc-400">
                      <span className="font-bold text-zinc-500 uppercase tracking-widest text-[10px] mr-2 block mb-2">Data Sources</span>
                      <div className="flex flex-wrap gap-2">
                        {result.sources.map((s) => (
                          <div key={s.source_id} className="bg-white/5 px-3 py-1.5 rounded-md flex items-center border border-white/5 shadow-inner min-w-0 max-w-full">
                            <span className="text-cyan-400/90 font-medium mr-2 truncate">{s.name}</span>
                            {s.table && <span className="text-zinc-500 border-l border-white/10 pl-2 mr-2 shrink-0">{s.table}</span>}
                            {s.page && <span className="text-zinc-500 border-l border-white/10 pl-2 shrink-0">Page {s.page}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SQL */}
                  {result.generated_sql && (
                    <SqlPanel sql={result.generated_sql} />
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
