import React from 'react';
import type { HistoryItem as HistoryItemType } from '../../types';
import { SqlPanel } from '../workspace/SqlPanel';

interface HistoryDetailProps {
  item: HistoryItemType;
  onClose: () => void;
  onRunAgain: (question: string, sourceId?: string) => void;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

export const HistoryDetail: React.FC<HistoryDetailProps> = ({ 
  item, 
  onClose, 
  onRunAgain, 
  onDelete,
  isDeleting
}) => {
  const isSuccess = item.status === 'success';
  const date = new Date(item.created_at).toLocaleString();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#09090b]/80 backdrop-blur-sm">
      <div className="bg-zinc-900 border border-zinc-800/80 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-zinc-800/80 bg-zinc-900/50">
          <h2 className="text-lg font-semibold text-zinc-100">Query Details</h2>
          <button 
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-300 transition-colors p-1 rounded-full hover:bg-zinc-800"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          
          <div>
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">Question</span>
            <p className="text-xl font-medium text-zinc-100 mt-1">{item.question}</p>
          </div>

          <div className="flex flex-wrap gap-4 border-y border-zinc-800/80 py-4">
            <div className="bg-zinc-800/30 px-4 py-2 rounded-lg border border-zinc-800/80">
              <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">Status</span>
              <span className={`text-sm font-medium flex items-center gap-1.5 ${isSuccess ? 'text-emerald-500' : 'text-red-500'}`}>
                <span className={`w-2 h-2 rounded-full ${isSuccess ? 'bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)]' : 'bg-red-500 shadow-[0_0_5px_rgba(239,68,68,0.5)]'}`}></span>
                {isSuccess ? 'Success' : 'Error'}
              </span>
            </div>
            
            <div className="bg-zinc-800/30 px-4 py-2 rounded-lg border border-zinc-800/80">
              <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">Date</span>
              <span className="text-sm font-medium text-zinc-300">{date}</span>
            </div>

            {isSuccess && (
              <>
                <div className="bg-zinc-800/30 px-4 py-2 rounded-lg border border-zinc-800/80">
                  <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">Rows</span>
                  <span className="text-sm font-medium text-zinc-300">{item.row_count}</span>
                </div>
                <div className="bg-zinc-800/30 px-4 py-2 rounded-lg border border-zinc-800/80">
                  <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">Time</span>
                  <span className="text-sm font-medium text-zinc-300">{item.execution_time_ms}ms</span>
                </div>
              </>
            )}
          </div>

          {!isSuccess && item.error && (
            <div>
              <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-2">Error Details</span>
              <div className="bg-red-500/10 text-red-400 border border-red-500/20 p-4 rounded-lg text-sm font-medium">
                {item.error}
              </div>
            </div>
          )}

          {item.generated_sql && (
            <div className="rounded-xl overflow-hidden border border-zinc-800/80 shadow-[0_0_15px_rgba(0,0,0,0.2)]">
              <SqlPanel sql={item.generated_sql} />
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-zinc-800/80 bg-zinc-900/80 flex items-center justify-between">
          <button 
            onClick={() => onDelete(item.id)}
            disabled={isDeleting}
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10 px-4 py-2 rounded-lg transition-colors text-sm font-medium flex items-center disabled:opacity-50"
          >
            {isDeleting ? (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-red-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            )}
            Delete Record
          </button>
          
          <div className="flex gap-3">
            <button 
              onClick={onClose}
              className="px-6 py-2 rounded-lg font-medium text-zinc-300 bg-zinc-800 hover:bg-zinc-700 transition-colors"
            >
              Close
            </button>
    <button 
      onClick={() => {
        onRunAgain(item.question, item.source_id);
        onClose();
      }}
      className="px-6 py-2 rounded-lg font-medium text-zinc-950 bg-cyan-500 hover:bg-cyan-400 transition-all shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:scale-105 flex items-center"
    >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Run Again
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
