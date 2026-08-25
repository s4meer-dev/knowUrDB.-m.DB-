import React from 'react';
import type { HistoryItem as HistoryItemType } from '../../types';

interface HistoryItemProps {
  item: HistoryItemType;
  onClick: () => void;
}

export const HistoryItem: React.FC<HistoryItemProps> = ({ item, onClick }) => {
  const isSuccess = item.status === 'success';
  const date = new Date(item.created_at).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
  });

  return (
    <div 
      onClick={onClick}
      className="bg-zinc-900/50 backdrop-blur-md rounded-xl shadow-sm border border-zinc-800/80 p-4 hover:border-cyan-500/50 hover:bg-zinc-800/80 hover:shadow-[0_0_15px_rgba(34,211,238,0.1)] transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          {isSuccess ? (
            <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0 shadow-[0_0_5px_rgba(16,185,129,0.5)]"></span>
          ) : (
            <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0 shadow-[0_0_5px_rgba(239,68,68,0.5)]"></span>
          )}
          <h3 className="font-medium text-zinc-200 truncate" title={item.question}>
            {item.question}
          </h3>
        </div>
        <div className="flex items-center gap-4 text-xs text-zinc-500 ml-4 font-medium">
          <span>{date}</span>
          {isSuccess && <span>{item.row_count} row{item.row_count !== 1 ? 's' : ''}</span>}
          {isSuccess && <span>{item.execution_time_ms}ms</span>}
          {item.query_source && <span className="capitalize">{item.query_source}</span>}
        </div>
      </div>
      
      <div className="flex items-center text-cyan-400 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
        <span className="text-sm font-semibold mr-1">View</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </div>
    </div>
  );
};
