import React from 'react';
import type { HistoryItem as HistoryItemType } from '../../types';
import { SqlPanel } from '../workspace/SqlPanel';

interface HistoryDetailProps {
  item: HistoryItemType;
  onClose: () => void;
  onRunAgain: (question: string) => void;
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Query Details</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          
          <div>
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Question</span>
            <p className="text-xl font-medium text-gray-800 mt-1">{item.question}</p>
          </div>

          <div className="flex flex-wrap gap-4 border-y border-gray-100 py-4">
            <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
              <span className="text-xs text-gray-500 block mb-1">Status</span>
              <span className={`text-sm font-medium flex items-center gap-1.5 ${isSuccess ? 'text-green-600' : 'text-red-600'}`}>
                <span className={`w-2 h-2 rounded-full ${isSuccess ? 'bg-green-500' : 'bg-red-500'}`}></span>
                {isSuccess ? 'Success' : 'Error'}
              </span>
            </div>
            
            <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
              <span className="text-xs text-gray-500 block mb-1">Date</span>
              <span className="text-sm font-medium text-gray-700">{date}</span>
            </div>

            {isSuccess && (
              <>
                <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
                  <span className="text-xs text-gray-500 block mb-1">Rows</span>
                  <span className="text-sm font-medium text-gray-700">{item.row_count}</span>
                </div>
                <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
                  <span className="text-xs text-gray-500 block mb-1">Time</span>
                  <span className="text-sm font-medium text-gray-700">{item.execution_time_ms}ms</span>
                </div>
              </>
            )}
          </div>

          {!isSuccess && item.error && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">Error Details</span>
              <div className="bg-red-50 text-red-700 border border-red-200 p-4 rounded-lg text-sm">
                {item.error}
              </div>
            </div>
          )}

          {item.generated_sql && (
            <div className="rounded-xl overflow-hidden border border-gray-200">
              <SqlPanel sql={item.generated_sql} />
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <button 
            onClick={() => onDelete(item.id)}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-800 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors text-sm font-medium flex items-center disabled:opacity-50"
          >
            {isDeleting ? (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
              className="px-6 py-2 rounded-lg font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
            <button 
              onClick={() => {
                onRunAgain(item.question);
                onClose();
              }}
              className="px-6 py-2 rounded-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-sm flex items-center"
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
