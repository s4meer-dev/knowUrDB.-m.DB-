import React from 'react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, any>[];
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ columns, rows }) => {
  if (columns.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 bg-gray-50 m-4 rounded-xl border border-gray-200">
        <p>No columns returned from the query.</p>
      </div>
    );
  }

  return (
    <div className="min-w-full overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
        <thead className="bg-gray-50 sticky top-0 shadow-sm z-10">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className="px-6 py-3 font-semibold text-gray-700 tracking-wider whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {rows.map((row, rIdx) => (
            <tr key={rIdx} className="hover:bg-gray-50 transition-colors">
              {columns.map((col, cIdx) => (
                <td key={cIdx} className="px-6 py-4 whitespace-nowrap text-gray-600 max-w-xs truncate" title={row[col] !== null ? String(row[col]) : ''}>
                  {row[col] !== null ? String(row[col]) : <span className="text-gray-400 italic">null</span>}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500 bg-gray-50">
                <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <p className="text-base font-medium text-gray-600">No records found</p>
                <p className="text-sm mt-1">The query executed successfully but returned 0 rows.</p>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};
