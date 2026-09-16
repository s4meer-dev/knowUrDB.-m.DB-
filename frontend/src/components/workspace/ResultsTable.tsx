import React, { useState, useMemo } from 'react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, any>[];
  pageSize?: number;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ columns, rows, pageSize = 50 }) => {
  const [currentPage, setCurrentPage] = useState(1);

  if (columns.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400 bg-zinc-900/50 rounded-xl border border-zinc-800/80">
        <p>No columns returned from the query.</p>
      </div>
    );
  }

  // Determine if a column is numeric to right-align it
  const isNumeric = (colName: string) => {
    if (rows.length === 0) return false;
    const val = rows[0][colName];
    return typeof val === 'number' && !isNaN(val);
  };

  const totalPages = Math.ceil(rows.length / pageSize);
  
  const currentRows = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return rows.slice(startIndex, startIndex + pageSize);
  }, [rows, currentPage, pageSize]);

  return (
    <div className="rounded-xl border border-zinc-800/60 shadow-lg relative bg-zinc-950/40 overflow-hidden flex flex-col">
      <div className="max-h-[400px] overflow-auto custom-scrollbar">
        <table className="min-w-full divide-y divide-zinc-800 text-sm text-left relative z-10 border-collapse">
          <thead className="bg-zinc-900/90 backdrop-blur-md sticky top-0 z-20 shadow-sm shadow-black/50">
            <tr>
              {columns.map((col, idx) => (
                <th 
                  key={idx} 
                  className={`px-4 py-3 font-semibold text-zinc-300 tracking-wider whitespace-nowrap uppercase text-[10px] ${isNumeric(col) ? 'text-right' : 'text-left'}`}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/30">
            {currentRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-zinc-800/40 transition-colors group cursor-default">
                {columns.map((col, cIdx) => (
                  <td 
                    key={cIdx} 
                    className={`px-4 py-3 whitespace-nowrap text-zinc-400 group-hover:text-zinc-200 transition-colors max-w-xs truncate ${isNumeric(col) ? 'text-right font-mono text-[13px]' : 'text-left'}`} 
                    title={row[col] !== null ? String(row[col]) : ''}
                  >
                    {row[col] !== null ? String(row[col]) : <span className="text-zinc-600 italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-6 py-16 text-center text-zinc-500 bg-zinc-900/20">
                  <svg className="w-12 h-12 mx-auto text-zinc-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                  </svg>
                  <p className="text-base font-semibold text-zinc-300">No records found</p>
                  <p className="text-sm mt-1">The query executed successfully but returned 0 rows.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/90 border-t border-zinc-800/60 z-20">
          <div className="text-xs text-zinc-400">
            Showing <span className="font-semibold text-zinc-200">{(currentPage - 1) * pageSize + 1}</span> to <span className="font-semibold text-zinc-200">{Math.min(currentPage * pageSize, rows.length)}</span> of <span className="font-semibold text-zinc-200">{rows.length}</span> results
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-zinc-700/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
            >
              Previous
            </button>
            <button 
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-zinc-700/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
