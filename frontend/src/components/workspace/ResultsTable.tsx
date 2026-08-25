import React from 'react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, any>[];
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ columns, rows }) => {
  if (columns.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400 bg-zinc-900/50 m-4 rounded-xl border border-zinc-800/80">
        <p>No columns returned from the query.</p>
      </div>
    );
  }

  return (
    <div className="min-w-full overflow-x-auto">
      <table className="min-w-full divide-y divide-zinc-800 text-sm text-left">
        <thead className="bg-zinc-900/90 sticky top-0 shadow-sm z-10 backdrop-blur-md">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className="px-6 py-4 font-semibold text-zinc-300 tracking-wider whitespace-nowrap border-b border-zinc-800/80">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-zinc-900/30 divide-y divide-zinc-800/50">
          {rows.map((row, rIdx) => (
            <tr key={rIdx} className="hover:bg-zinc-800/40 transition-colors">
              {columns.map((col, cIdx) => (
                <td key={cIdx} className="px-6 py-4 whitespace-nowrap text-zinc-400 max-w-xs truncate" title={row[col] !== null ? String(row[col]) : ''}>
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
  );
};
