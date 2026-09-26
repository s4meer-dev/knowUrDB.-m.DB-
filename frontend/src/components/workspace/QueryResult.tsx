import React, { useState, useEffect } from 'react';
import type { ClarificationCandidate, QueryResponse } from '../../types';
import { ResultsTable } from './ResultsTable';
import { SqlPanel } from './SqlPanel';
import { ErrorState } from '../common/ErrorState';
import { VisualizationEngine } from './VisualizationEngine';

interface QueryResultProps {
  result: QueryResponse | null;
  isLoading: boolean;
  canGoBack?: boolean;
  onBack?: () => void;
  onChangeCollection?: () => void;
  onSelectCollection: (collectionName: string, sourceId?: string) => void;
  onFollowUp: (question: string, sourceIds?: string[], activeCollection?: string) => void;
}

const LOADING_STEPS = [
  'Understanding question...',
  'Checking dataset catalog...',
  'Identifying collection...',
  'Building MongoDB pipeline...',
  'Preparing answer...',
];

export const QueryResult: React.FC<QueryResultProps> = ({
  result,
  isLoading,
  canGoBack = false,
  onBack,
  onChangeCollection,
  onSelectCollection,
  onFollowUp,
}) => {
  const [showTechDetails, setShowTechDetails] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<number>(0);

  useEffect(() => {
    if (!isLoading) {
      setLoadingStep(0);
      return;
    }
    const timer = setInterval(() => {
      setLoadingStep((prev) => (prev < LOADING_STEPS.length - 1 ? prev + 1 : prev));
    }, 240);
    return () => clearInterval(timer);
  }, [isLoading]);

  if (!result && !isLoading) {
    return null;
  }

  // Contextual Loading Experience
  if (isLoading && !result) {
    return (
      <div className="bg-[#09090b]/90 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.8)] border border-zinc-800/80 p-8 mt-6 animate-in fade-in duration-200 relative overflow-hidden">
        <div className="max-w-md mx-auto flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mb-4">
            <svg
              className="animate-spin h-5 w-5 text-cyan-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <p className="text-sm font-medium text-zinc-200 tracking-wide mb-4">
            {LOADING_STEPS[loadingStep]}
          </p>
          <div className="flex items-center gap-2">
            {LOADING_STEPS.map((_, idx) => (
              <span
                key={idx}
                className={`h-1.5 rounded-full transition-all duration-200 ${
                  idx <= loadingStep ? 'w-6 bg-cyan-400' : 'w-2 bg-zinc-800'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const mongoPipelineCode = result.generated_mongo_query || result.generated_sql;
  const pres = result.presentation;
  const uiType =
    pres?.type || (result.row_count === 1 && result.columns.length === 1 ? 'kpi' : 'table');
  const isFieldUnavailable =
    result.intent === 'FIELD_NOT_AVAILABLE' ||
    result.error_code === 'FIELD_NOT_AVAILABLE' ||
    uiType === 'field_unavailable';
  const isNoMatches =
    result.intent === 'NO_MATCHING_RECORDS' ||
    uiType === 'no_matches';
  const isClarification =
    (result.status === 'clarification_required' || uiType === 'clarification') &&
    !isFieldUnavailable &&
    !isNoMatches;
  const headerTitle = isClarification
    ? 'NEED A LITTLE MORE CONTEXT'
    : isFieldUnavailable
    ? 'FIELD NOT AVAILABLE'
    : isNoMatches
    ? 'NO MATCHING RECORDS'
    : pres?.title || result.answer?.headline || 'Results';
  const summaryText = pres?.summary || result.answer?.summary || '';
  const candidateCollections: ClarificationCandidate[] =
    result.candidates && result.candidates.length > 0
      ? result.candidates
      : pres?.candidate_collections || [];

  return (
    <div className="bg-[#09090b]/90 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.8)] border border-zinc-800/80 flex flex-col mt-6 animate-in slide-in-from-bottom-2 fade-in duration-250 ease-out relative overflow-hidden ring-1 ring-white/5">
      <div className="absolute inset-0 bg-gradient-to-b from-cyan-900/5 to-transparent pointer-events-none" />

      {/* 1. Result / Clarification Header Bar with Back & Using <Collection> [Change] */}
      <div className="bg-zinc-900/40 border-b border-zinc-800/60 px-6 py-3.5 flex flex-wrap items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-3">
          {canGoBack && onBack && (
            <button
              type="button"
              onClick={onBack}
              aria-label="Go back"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-300 hover:text-cyan-300 bg-zinc-800/70 hover:bg-cyan-500/15 border border-zinc-700/60 hover:border-cyan-500/30 px-2.5 py-1 rounded-lg transition-all"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
          )}
          <div className="relative flex h-2 w-2">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
          </div>
          <h2 className="font-semibold text-zinc-100 tracking-tight text-[14px] uppercase">
            {isLoading ? LOADING_STEPS[loadingStep] : headerTitle}
          </h2>
        </div>

        {/* Active Collection Context Indicator + [Change] Button */}
        {!isClarification && result.collection && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-400">Using:</span>
            <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/25">
              {result.collection}
            </span>
            {onChangeCollection && (
              <button
                type="button"
                onClick={onChangeCollection}
                className="text-xs text-zinc-400 hover:text-cyan-300 underline underline-offset-4 decoration-zinc-700 hover:decoration-cyan-400 px-1.5 py-0.5 transition-colors"
              >
                Change
              </button>
            )}
          </div>
        )}
      </div>

      <div
        className={`transition-opacity duration-200 flex flex-col p-6 overflow-hidden relative z-10 ${
          isLoading ? 'opacity-40 pointer-events-none' : 'opacity-100'
        }`}
      >
        {/* ==============================================================
            CLARIFICATION VIEW (NEED A LITTLE MORE CONTEXT)
           ============================================================== */}
        {isClarification ? (
          <div className="py-2 animate-in fade-in duration-200">
            <p className="text-zinc-200 text-[15px] leading-relaxed mb-6">
              {result.error || summaryText || 'I found multiple options. Which one would you like to use?'}
            </p>

            {(() => {
              const clarType =
                pres?.clarification_type ||
                (candidateCollections[0] as any)?.clarification_type ||
                'collection';
              const actionLabel =
                clarType === 'field'
                  ? 'Select field'
                  : clarType === 'dataset'
                  ? 'Select dataset'
                  : 'Select collection';
              const tipText =
                clarType === 'field'
                  ? 'Tip: You can also specify the field directly (e.g., "by loan_amount").'
                  : clarType === 'dataset'
                  ? 'Tip: You can also choose the dataset from the Sources dropdown.'
                  : 'Tip: You can also type the collection name directly above (e.g., "customers").';

              return (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                    {candidateCollections.map((c, idx) => {
                      const colKey = c.collection || c.name.toLowerCase();
                      const handleClick = () => {
                        if (clarType === 'field') {
                          onFollowUp(`${result.question} using ${c.name}`);
                        } else {
                          onSelectCollection(colKey, c.source_id);
                        }
                      };

                      return (
                        <button
                          key={idx}
                          type="button"
                          onClick={handleClick}
                          className="text-left bg-zinc-900/70 hover:bg-cyan-500/[0.08] border border-zinc-800/90 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 flex flex-col justify-between group focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
                        >
                          <div>
                            <div className="flex items-center justify-between gap-2 mb-2">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-zinc-100 group-hover:text-cyan-300 text-base tracking-tight capitalize transition-colors">
                                  {c.collection || c.name}
                                </span>
                                {c.filter_field_status && (
                                  <span
                                    className={`text-[10px] font-mono font-medium px-1.5 py-0.5 rounded border ${
                                      c.has_filter_field !== false
                                        ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                                        : 'bg-zinc-800/80 text-zinc-400 border-zinc-700/60'
                                    }`}
                                  >
                                    {c.filter_field_status}
                                  </span>
                                )}
                              </div>
                              {c.document_count !== undefined && c.document_count !== null && (
                                <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 shrink-0">
                                  {c.document_count.toLocaleString('en-IN')} docs
                                </span>
                              )}
                            </div>
                            {c.description && (
                              <p className="text-xs text-zinc-400 line-clamp-2 mb-3 leading-relaxed">
                                {c.description}
                              </p>
                            )}
                          </div>

                          <div>
                            {c.fields_preview && c.fields_preview.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-3">
                                {c.fields_preview.slice(0, 5).map((f) => (
                                  <span
                                    key={f}
                                    className="text-[10px] font-mono bg-black/40 border border-zinc-800 px-1.5 py-0.5 rounded text-zinc-400"
                                  >
                                    {f}
                                  </span>
                                ))}
                              </div>
                            )}
                            <div className="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-xs font-medium text-cyan-400/80 group-hover:text-cyan-300">
                              <span>{actionLabel}</span>
                              <svg
                                className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                              </svg>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {onBack && (
                    <div className="mt-6 pt-4 border-t border-zinc-800/60 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={onBack}
                        className="inline-flex items-center gap-2 text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 px-3.5 py-2 rounded-lg transition-colors"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                        </svg>
                        Back
                      </button>
                      <span className="text-[11px] text-zinc-500">{tipText}</span>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        ) : isFieldUnavailable ? (
          <div className="py-2 animate-in fade-in duration-200 space-y-6">
            <div className="bg-amber-500/[0.06] border border-amber-500/30 rounded-2xl p-6 sm:p-7 relative overflow-hidden">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-zinc-100 mb-1.5 flex items-center gap-2">
                    Field Not Available
                    {pres?.missing_field && (
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        {pres.missing_field}
                      </span>
                    )}
                  </h3>
                  <p className="text-zinc-300 text-sm leading-relaxed">
                    {summaryText || result.error || `The '${result.collection}' collection does not contain a '${pres?.missing_field || 'requested'}' field.`}
                  </p>
                </div>
              </div>

              {/* Available Fields in Current Collection */}
              {pres?.available_fields && pres.available_fields.length > 0 && (
                <div className="mt-5 pt-5 border-t border-amber-500/20">
                  <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
                    Available fields in {result.collection || 'this collection'} ({pres.available_fields.length}):
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {pres.available_fields.map((fld) => (
                      <span
                        key={fld}
                        className="text-xs font-mono bg-black/50 border border-zinc-800 px-2.5 py-1 rounded-md text-zinc-300 hover:border-cyan-500/30 transition-colors"
                      >
                        {fld}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Candidate Collections that DO have this field */}
            {candidateCollections.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3">
                  Collections containing '{pres?.missing_field || 'this field'}'
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {candidateCollections.map((c, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSelectCollection(c.collection || c.name.toLowerCase(), c.source_id)}
                      className="text-left bg-zinc-900/70 hover:bg-cyan-500/[0.08] border border-zinc-800 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 flex flex-col justify-between group"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="font-semibold text-zinc-100 group-hover:text-cyan-300 text-base tracking-tight capitalize transition-colors">
                            {c.collection || c.name}
                          </span>
                          {c.filter_field_status && (
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                              {c.filter_field_status}
                            </span>
                          )}
                        </div>
                        {c.document_count !== undefined && c.document_count !== null && (
                          <div className="text-xs font-mono text-zinc-400 mb-2">
                            {c.document_count.toLocaleString('en-IN')} documents
                          </div>
                        )}
                        {c.description && (
                          <p className="text-xs text-zinc-400 line-clamp-2 mb-3 leading-relaxed">
                            {c.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-xs font-medium text-cyan-400 group-hover:text-cyan-300">
                        <span>Select this collection</span>
                        <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              {onBack && (
                <button
                  type="button"
                  onClick={onBack}
                  className="inline-flex items-center gap-2 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 px-4 py-2 rounded-lg transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  Back
                </button>
              )}
              {onChangeCollection && (
                <button
                  type="button"
                  onClick={onChangeCollection}
                  className="text-xs bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/80 px-4 py-2 rounded-lg transition-colors"
                >
                  Choose Another Collection
                </button>
              )}
              {result.collection && (
                <button
                  type="button"
                  onClick={() => onFollowUp(`Show all ${result.collection}`)}
                  className="text-xs bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 px-4 py-2 rounded-lg transition-colors"
                >
                  Show All {result.collection} (Unfiltered)
                </button>
              )}
            </div>
          </div>
        ) : isNoMatches ? (
          <div className="py-2 animate-in fade-in duration-200 space-y-6">
            <div className="bg-zinc-900/70 border border-zinc-800 rounded-2xl p-6 sm:p-7 relative overflow-hidden">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-zinc-100 mb-1.5 flex items-center gap-2">
                    0 Matching Records
                    {pres?.field && pres?.requested_value && (
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                        {pres.field} = '{pres.requested_value}'
                      </span>
                    )}
                  </h3>
                  <p className="text-zinc-300 text-sm leading-relaxed">
                    {summaryText || `No records in '${result.collection}' match your filter.`}
                  </p>
                </div>
              </div>

              {/* Available Distinct Values */}
              {pres?.available_values && pres.available_values.length > 0 && (
                <div className="mt-5 pt-5 border-t border-zinc-800/80">
                  <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
                    Available {pres.field || 'distinct'} values in {result.collection || 'collection'}:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {pres.available_values.map((val) => (
                      <button
                        key={String(val)}
                        type="button"
                        onClick={() =>
                          onFollowUp(
                            `Show all ${result.collection} where ${pres.field || 'status'} is ${val}`,
                            undefined,
                            result.collection
                          )
                        }
                        className="inline-flex items-center gap-1.5 text-xs font-mono bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-3 py-1.5 rounded-lg transition-all group"
                      >
                        <span>'{String(val)}'</span>
                        <svg className="w-3 h-3 text-cyan-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-2">
                    Click any value above to filter records by that value.
                  </p>
                </div>
              )}
            </div>

            {/* Candidate Collections */}
            {candidateCollections.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3">
                  Other collections you can check
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {candidateCollections.map((c, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSelectCollection(c.collection || c.name.toLowerCase(), c.source_id)}
                      className="text-left bg-zinc-900/70 hover:bg-cyan-500/[0.08] border border-zinc-800 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 flex flex-col justify-between group"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="font-semibold text-zinc-100 group-hover:text-cyan-300 text-base tracking-tight capitalize transition-colors">
                            {c.collection || c.name}
                          </span>
                          {c.filter_field_status && (
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                              {c.filter_field_status}
                            </span>
                          )}
                        </div>
                        {c.document_count !== undefined && c.document_count !== null && (
                          <div className="text-xs font-mono text-zinc-400 mb-2">
                            {c.document_count.toLocaleString('en-IN')} documents
                          </div>
                        )}
                        {c.description && (
                          <p className="text-xs text-zinc-400 line-clamp-2 mb-3 leading-relaxed">
                            {c.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-xs font-medium text-cyan-400 group-hover:text-cyan-300">
                        <span>Select this collection</span>
                        <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              {onBack && (
                <button
                  type="button"
                  onClick={onBack}
                  className="inline-flex items-center gap-2 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 px-4 py-2 rounded-lg transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  Back
                </button>
              )}
              {onChangeCollection && (
                <button
                  type="button"
                  onClick={onChangeCollection}
                  className="text-xs bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/80 px-4 py-2 rounded-lg transition-colors"
                >
                  Change Collection
                </button>
              )}
              {result.collection && (
                <button
                  type="button"
                  onClick={() => onFollowUp(`Show all ${result.collection}`)}
                  className="text-xs bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 px-4 py-2 rounded-lg transition-colors"
                >
                  Show All {result.collection}
                </button>
              )}
            </div>
          </div>
        ) : result.status === 'error' ? (
          result.error_code === 'UNRELATED_QUERY' ? (
            <div className="flex flex-col items-center justify-center text-center py-8 px-4">
              <div className="w-14 h-14 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center mb-4">
                <svg className="w-7 h-7 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-zinc-200 mb-1.5">Outside Active Dataset Scope</h3>
              <p className="text-zinc-400 text-sm max-w-md leading-relaxed mb-5">{result.error}</p>
              <div className="flex flex-wrap justify-center gap-2">
                {onBack && (
                  <button
                    type="button"
                    onClick={onBack}
                    className="text-xs bg-zinc-800/70 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 px-3.5 py-2 rounded-lg transition-colors"
                  >
                    ← Back
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => onFollowUp('Give me info about dataset')}
                  className="text-xs bg-zinc-800/70 hover:bg-cyan-500/15 text-zinc-300 hover:text-cyan-300 border border-zinc-700/60 px-3.5 py-2 rounded-lg transition-colors"
                >
                  View dataset overview
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <ErrorState
                title={
                  result.error_code === 'UNSAFE_SQL' || result.error_code === 'UNSAFE_QUERY'
                    ? 'Read-Only Safety Guard'
                    : 'Could Not Complete Request'
                }
                message={
                  result.error || 'Please try rephrasing your question or checking the available fields.'
                }
                type="error"
              />
              {onBack && (
                <div>
                  <button
                    type="button"
                    onClick={onBack}
                    className="text-xs bg-zinc-800/70 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 px-3.5 py-2 rounded-lg transition-colors"
                  >
                    ← Back
                  </button>
                </div>
              )}
            </div>
          )
        ) : (
          <>
            {/* Multi-Collection Data Sources Banner (when query joins multiple collections) */}
            {pres?.multi_collection_sources && pres.multi_collection_sources.length >= 2 && (
              <div className="mb-4 bg-zinc-900/60 border border-cyan-500/20 rounded-xl px-4 py-2.5 flex flex-wrap items-center gap-2 text-xs">
                <span className="font-bold text-zinc-400 uppercase tracking-wider text-[10px]">
                  Data Sources:
                </span>
                {pres.multi_collection_sources.map((srcName, idx) => (
                  <React.Fragment key={srcName}>
                    <span className="font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {srcName}
                    </span>
                    {idx < pres.multi_collection_sources!.length - 1 && (
                      <span className="text-zinc-500 font-mono">↔</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}

            {/* ==============================================================
                MODE 1: KPI RESULT (COUNT, SINGLE AVERAGE, SINGLE SUM)
               ============================================================== */}
            {uiType === 'kpi' && (
              <div className="py-2">
                <div className="bg-gradient-to-br from-zinc-900/90 to-[#0c0c10] border border-cyan-500/20 rounded-2xl p-6 sm:p-8 shadow-inner max-w-lg">
                  <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-widest mb-2">
                    {headerTitle}
                  </div>
                  <div className="flex items-baseline gap-3 flex-wrap">
                    <span className="text-4xl sm:text-5xl font-semibold text-white tracking-tight font-mono drop-shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                      {pres?.primary_value || result.answer?.value}
                    </span>
                    <span className="text-base sm:text-lg text-zinc-400 font-normal">
                      {pres?.primary_unit || result.answer?.unit}
                    </span>
                  </div>
                  {summaryText && (
                    <p className="text-zinc-300 text-sm mt-4 leading-relaxed border-t border-zinc-800/80 pt-3">
                      {summaryText}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ==============================================================
                MODE 2: DATASET OVERVIEW / COLLECTION OVERVIEW
               ============================================================== */}
            {(uiType === 'dataset_overview' || uiType === 'collection_overview') && (
              <div className="space-y-6">
                {summaryText && (
                  <p className="text-zinc-200 text-[15px] leading-relaxed">{summaryText}</p>
                )}

                {pres?.collections_summary && pres.collections_summary.length > 0 ? (
                  <div>
                    <h4 className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest mb-3">
                      Collections ({pres.collections_summary.length})
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {pres.collections_summary.map((col) => (
                        <button
                          key={col.collection}
                          type="button"
                          onClick={() =>
                            onFollowUp(`Show me ${col.collection}`, undefined, col.collection)
                          }
                          className="text-left bg-zinc-900/60 hover:bg-cyan-500/10 border border-zinc-800 hover:border-cyan-500/30 rounded-xl p-4 transition-all group"
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono font-semibold text-zinc-100 group-hover:text-cyan-300 text-sm">
                              {col.collection}
                            </span>
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                              {col.documents.toLocaleString('en-IN')} docs
                            </span>
                          </div>
                          <div className="text-xs text-zinc-400 mb-2">{col.fields} schema fields</div>
                          <div className="text-[11px] text-zinc-500 truncate font-mono">
                            {col.key_fields}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  result.rows.length > 0 && <ResultsTable columns={result.columns} rows={result.rows} />
                )}
              </div>
            )}

            {/* ==============================================================
                MODE 2B: DATASET LIST (REGISTERED DATASETS)
               ============================================================== */}
            {uiType === 'dataset_list' && (
              <div className="space-y-6">
                {summaryText && (
                  <p className="text-zinc-200 text-[15px] leading-relaxed">{summaryText}</p>
                )}

                {pres?.datasets_summary && pres.datasets_summary.length > 0 ? (
                  <div>
                    <h4 className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest mb-3">
                      Registered Datasets ({pres.datasets_summary.length})
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                      {pres.datasets_summary.map((ds) => (
                        <div
                          key={ds.dataset}
                          className="bg-zinc-900/70 border border-zinc-800 hover:border-cyan-500/40 rounded-xl p-4 transition-all duration-200 flex flex-col justify-between group"
                        >
                          <div>
                            <div className="flex items-center justify-between gap-2 mb-2">
                              <span className="font-semibold text-zinc-100 group-hover:text-cyan-300 text-base tracking-tight">
                                {ds.dataset}
                              </span>
                              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                                {ds.domain}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-zinc-400 mb-3 font-mono">
                              <span>
                                {typeof ds.collections === 'number'
                                  ? `${ds.collections} collections`
                                  : 'Active Collections'}
                              </span>
                              <span>•</span>
                              <span>{ds.documents.toLocaleString('en-IN')} docs</span>
                            </div>
                            {typeof ds.collections === 'string' && ds.collections && (
                              <p className="text-xs text-zinc-500 font-mono line-clamp-2 mb-3">
                                {ds.collections}
                              </p>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() =>
                              onFollowUp(
                                `Tell me about ${ds.dataset}`,
                                ds.source_id ? [ds.source_id] : undefined
                              )
                            }
                            className="w-full flex items-center justify-center gap-1.5 pt-2.5 border-t border-zinc-800/80 text-xs font-medium text-cyan-400/90 hover:text-cyan-300 transition-colors"
                          >
                            <span>Explore Dataset</span>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  result.rows.length > 0 && <ResultsTable columns={result.columns} rows={result.rows} />
                )}
              </div>
            )}

            {/* ==============================================================
                MODE 3: SINGLE RECORD DETAIL (MAXIMUM / MINIMUM)
               ============================================================== */}
            {uiType === 'detail' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-zinc-900/90 to-[#0c0c10] border border-cyan-500/20 rounded-2xl p-6">
                  <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-widest mb-1.5">
                    {headerTitle}
                  </div>
                  <div className="flex items-baseline gap-3 flex-wrap mb-3">
                    <span className="text-3xl sm:text-4xl font-semibold text-white font-mono">
                      {pres?.primary_value || result.answer?.value}
                    </span>
                    <span className="text-base text-cyan-300 font-medium">
                      {pres?.primary_unit || result.answer?.unit}
                    </span>
                  </div>
                  {summaryText && (
                    <p className="text-zinc-300 text-sm leading-relaxed">{summaryText}</p>
                  )}

                  {pres?.highlight_record && (
                    <div className="mt-5 pt-4 border-t border-zinc-800/80 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                      {Object.entries(pres.highlight_record).map(([k, v]) => (
                        <div
                          key={k}
                          className="bg-black/40 border border-zinc-800/70 rounded-lg px-3 py-2"
                        >
                          <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">
                            {k.replace(/_/g, ' ')}
                          </span>
                          <span className="text-xs font-mono text-zinc-200 truncate block mt-0.5">
                            {typeof v === 'number' ? v.toLocaleString('en-IN') : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ==============================================================
                MODE 4: TABLE / RANKED TABLE / COMPARISON / CHART / SCHEMA
               ============================================================== */}
            {(uiType === 'table' ||
              uiType === 'ranked_table' ||
              uiType === 'comparison' ||
              uiType === 'chart' ||
              uiType === 'schema') && (
              <div className="space-y-5">
                {summaryText && (
                  <p className="text-zinc-200 text-[15px] leading-relaxed">{summaryText}</p>
                )}

                {(uiType === 'ranked_table' || uiType === 'comparison' || uiType === 'chart') &&
                  result.columns.length >= 2 &&
                  result.rows.length > 0 && (
                    <VisualizationEngine
                      columns={result.columns}
                      rows={result.rows}
                      mode={uiType}
                    />
                  )}

                {result.columns.length > 0 && result.rows.length > 0 && (
                  <ResultsTable columns={result.columns} rows={result.rows} />
                )}
              </div>
            )}

            {/* ==============================================================
                MODE 5: DOCUMENT RAG ANSWER
               ============================================================== */}
            {uiType === 'document_answer' && (
              <div className="space-y-5">
                <div className="bg-zinc-900/60 border border-cyan-500/20 rounded-xl p-5">
                  <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-widest mb-2">
                    Document Answer • {pres?.primary_value}
                  </div>
                  <p className="text-zinc-100 text-[15px] leading-relaxed whitespace-pre-line">
                    {summaryText}
                  </p>
                </div>
                {result.rows.length > 0 && (
                  <ResultsTable columns={result.columns} rows={result.rows} />
                )}
              </div>
            )}

            {/* ==============================================================
                MODE 6: EMPTY RESULT EXPERIENCE
               ============================================================== */}
            {uiType === 'empty' && (
              <div className="flex flex-col items-center justify-center text-center py-10 px-4 bg-zinc-900/30 border border-zinc-800/60 rounded-xl">
                <svg
                  className="w-10 h-10 text-zinc-500 mb-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <h3 className="text-base font-semibold text-zinc-200 mb-1">No Matching Data</h3>
                <p className="text-sm text-zinc-400 max-w-md mb-4">
                  {summaryText || "I couldn't find any documents matching that filter."}
                </p>
                <div className="flex items-center gap-2">
                  {result.collection && (
                    <button
                      type="button"
                      onClick={() =>
                        onFollowUp(`Show me ${result.collection}`, undefined, result.collection)
                      }
                      className="text-xs bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 px-4 py-2 rounded-lg transition-colors"
                    >
                      Remove filter
                    </button>
                  )}
                  {onChangeCollection && (
                    <button
                      type="button"
                      onClick={onChangeCollection}
                      className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 px-4 py-2 rounded-lg transition-colors"
                    >
                      Change collection
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Secondary Technical Drawer (Collapsed by default) */}
            <div className="mt-6 border-t border-white/5 pt-4">
              <button
                type="button"
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="flex items-center text-xs font-semibold text-zinc-500 hover:text-cyan-400 uppercase tracking-widest transition-colors focus:outline-none"
              >
                <svg
                  className={`w-3.5 h-3.5 mr-2 transition-transform duration-200 ${
                    showTechDetails ? 'rotate-90 text-cyan-400' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
                Technical Details
              </button>

              {showTechDetails && (
                <div className="mt-4 space-y-4 animate-in fade-in duration-200">
                  <div className="flex flex-wrap gap-3">
                    {result.intent && (
                      <div className="bg-black/40 border border-white/5 rounded-lg px-3.5 py-2.5 flex flex-col">
                        <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">
                          Intent
                        </span>
                        <span className="text-cyan-300 font-mono text-xs mt-0.5">{result.intent}</span>
                      </div>
                    )}
                    <div className="bg-black/40 border border-white/5 rounded-lg px-3.5 py-2.5 flex flex-col">
                      <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">
                        Execution Time
                      </span>
                      <span className="text-zinc-300 font-mono text-xs mt-0.5">
                        {result.execution_time_ms} ms
                      </span>
                    </div>
                    <div className="bg-black/40 border border-white/5 rounded-lg px-3.5 py-2.5 flex flex-col">
                      <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">
                        Documents Returned
                      </span>
                      <span className="text-zinc-300 font-mono text-xs mt-0.5">{result.row_count}</span>
                    </div>
                    {result.collection && (
                      <div className="bg-black/40 border border-white/5 rounded-lg px-3.5 py-2.5 flex flex-col">
                        <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">
                          Collection
                        </span>
                        <span className="text-emerald-300 font-mono text-xs mt-0.5">
                          {result.collection}
                        </span>
                      </div>
                    )}
                  </div>

                  {mongoPipelineCode && <SqlPanel sql={mongoPipelineCode} />}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
