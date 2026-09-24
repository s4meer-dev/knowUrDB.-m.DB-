import React, { useState, useMemo } from 'react';

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, any>[];
  pageSize?: number;
}

const CURRENCY_COLS = new Set([
  'price',
  'salary',
  'total_spent',
  'total_amount',
  'amount',
  'revenue',
  'line_total',
  'average_price',
  'total_price',
  'average_salary',
  'total_salary',
]);

function formatCellValue(col: string, val: any): React.ReactNode {
  if (val === null || val === undefined) {
    return <span className="text-zinc-600 italic">null</span>;
  }

  const colLower = col.toLowerCase();

  // Rank badge
  if (colLower === 'rank' && typeof val === 'number') {
    const badgeColor =
      val === 1
        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
        : val === 2
        ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
        : val === 3
        ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
        : 'bg-zinc-800/80 text-zinc-400 border-zinc-700/50';
    return (
      <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-xs font-mono font-semibold border ${badgeColor}`}>
        #{val}
      </span>
    );
  }

  // Numbers
  if (typeof val === 'number' && !isNaN(val)) {
    const isCurrency = CURRENCY_COLS.has(colLower);
    const isPercent = colLower.includes('percentage') || colLower.includes('rate');
    if (isPercent) {
      return `${Number.isInteger(val) ? val : val.toFixed(1)}%`;
    }
    if (isCurrency) {
      return `₹${val.toLocaleString('en-IN', { maximumFractionDigits: Number.isInteger(val) ? 0 : 2 })}`;
    }
    return val.toLocaleString('en-IN', { maximumFractionDigits: Number.isInteger(val) ? 0 : 2 });
  }

  // Dates (YYYY-MM-DD or ISO string)
  if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}(T.*)?$/.test(val)) {
    const d = new Date(val);
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    }
  }

  // Nested Object or Array
  if (typeof val === 'object') {
    if (Array.isArray(val)) {
      return (
        <span className="inline-flex items-center gap-1 text-xs font-mono bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded text-cyan-300">
          [{val.length} {val.length === 1 ? 'item' : 'items'}]
        </span>
      );
    }
    const entries = Object.entries(val)
      .slice(0, 2)
      .map(([k, v]) => `${k}: ${String(v)}`)
      .join(' • ');
    return (
      <span className="text-xs text-zinc-300 bg-zinc-900/80 border border-zinc-800 px-2 py-0.5 rounded">
        {entries}
      </span>
    );
  }

  return String(val);
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ columns, rows, pageSize = 50 }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const sortedRows = useMemo(() => {
    if (!sortCol) return rows;
    return [...rows].sort((a, b) => {
      const va = a[sortCol];
      const vb = b[sortCol];
      if (va === vb) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortAsc ? va - vb : vb - va;
      }
      return sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
  }, [rows, sortCol, sortAsc]);

  const currentRows = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedRows.slice(startIndex, startIndex + pageSize);
  }, [sortedRows, currentPage, pageSize]);

  if (columns.length === 0) {
    return null;
  }

  const isNumeric = (colName: string) => {
    if (rows.length === 0 || colName.toLowerCase() === 'rank') return false;
    const val = rows[0][colName];
    return typeof val === 'number' && !isNaN(val);
  };

  const handleHeaderClick = (col: string) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(false);
    }
  };

  const handleCopyCell = (val: any, cellKey: string) => {
    if (val === null || val === undefined) return;
    const text = typeof val === 'object' ? JSON.stringify(val) : String(val);
    navigator.clipboard?.writeText(text);
    setCopiedCell(cellKey);
    setTimeout(() => setCopiedCell(null), 1200);
  };

  const totalPages = Math.ceil(sortedRows.length / pageSize);

  return (
    <div className="rounded-xl border border-zinc-800/70 shadow-lg relative bg-[#0b0b0e]/80 overflow-hidden flex flex-col">
      <div className="max-h-[440px] overflow-auto custom-scrollbar">
        <table className="min-w-full divide-y divide-zinc-800/80 text-sm text-left relative z-10 border-collapse">
          <thead className="bg-zinc-900/95 backdrop-blur-md sticky top-0 z-20 shadow-sm shadow-black/50">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() => handleHeaderClick(col)}
                  className={`px-4 py-3 font-semibold text-zinc-300 hover:text-cyan-300 cursor-pointer select-none tracking-wider whitespace-nowrap uppercase text-[11px] transition-colors ${
                    isNumeric(col) ? 'text-right' : 'text-left'
                  }`}
                >
                  <span className="inline-flex items-center gap-1.5">
                    {col.replace(/_/g, ' ')}
                    {sortCol === col && (
                      <span className="text-cyan-400 text-[10px]">
                        {sortAsc ? '▲' : '▼'}
                      </span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/40">
            {currentRows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-cyan-500/[0.04] transition-colors group"
              >
                {columns.map((col, cIdx) => {
                  const cellKey = `${rIdx}-${cIdx}`;
                  const rawVal = row[col];
                  return (
                    <td
                      key={cIdx}
                      onClick={() => handleCopyCell(rawVal, cellKey)}
                      className={`px-4 py-3 whitespace-nowrap text-zinc-300 group-hover:text-zinc-100 transition-colors max-w-xs truncate cursor-pointer ${
                        isNumeric(col) ? 'text-right font-mono text-[13px]' : 'text-left'
                      }`}
                      title={
                        copiedCell === cellKey
                          ? 'Copied!'
                          : rawVal !== null && rawVal !== undefined
                          ? typeof rawVal === 'object'
                            ? JSON.stringify(rawVal)
                            : String(rawVal)
                          : ''
                      }
                    >
                      {copiedCell === cellKey ? (
                        <span className="text-xs text-emerald-400 font-mono">Copied</span>
                      ) : (
                        formatCellValue(col, rawVal)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/90 border-t border-zinc-800/60 z-20">
          <div className="text-xs text-zinc-400">
            Showing <span className="font-semibold text-zinc-200">{(currentPage - 1) * pageSize + 1}</span> to{' '}
            <span className="font-semibold text-zinc-200">{Math.min(currentPage * pageSize, sortedRows.length)}</span> of{' '}
            <span className="font-semibold text-zinc-200">{sortedRows.length}</span> documents
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-zinc-700/50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-zinc-700/50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
