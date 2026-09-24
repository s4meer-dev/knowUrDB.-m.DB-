import React, { useMemo } from 'react';

interface VisualizationEngineProps {
  columns: string[];
  rows: Record<string, any>[];
  mode?: string;
}

export const VisualizationEngine: React.FC<VisualizationEngineProps> = ({
  columns,
  rows,
  mode,
}) => {
  const chartConfig = useMemo(() => {
    if (!rows || rows.length === 0 || rows.length > 25) return null;
    if (!columns || columns.length < 2) return null;

    // Identify string label column (prefer 'name', 'category', 'department', 'month', 'city', or first string col)
    const stringCols = columns.filter(
      (c) =>
        c.toLowerCase() !== 'rank' &&
        typeof rows[0][c] === 'string' &&
        !c.toLowerCase().endsWith('_id')
    );
    const fallbackLabelCol = columns.find((c) => c.toLowerCase() !== 'rank') || columns[0];
    const labelCol =
      stringCols.find((c) => ['name', 'category', 'department', 'month', 'city'].includes(c.toLowerCase())) ||
      stringCols[0] ||
      fallbackLabelCol;

    // Identify numeric metric columns (excluding 'rank')
    const numericCols = columns.filter(
      (c) =>
        c.toLowerCase() !== 'rank' &&
        c !== labelCol &&
        typeof rows[0][c] === 'number' &&
        !isNaN(rows[0][c])
    );

    if (numericCols.length === 0) return null;

    const primaryMetric = numericCols[0];
    const secondaryMetric = mode === 'comparison' && numericCols.length > 1 ? numericCols[1] : null;

    const maxPrimary = Math.max(...rows.map((r) => Number(r[primaryMetric]) || 0), 1);
    const maxSecondary = secondaryMetric
      ? Math.max(...rows.map((r) => Number(r[secondaryMetric]) || 0), 1)
      : 1;

    return {
      labelCol,
      primaryMetric,
      secondaryMetric,
      maxPrimary,
      maxSecondary,
    };
  }, [columns, rows, mode]);

  if (!chartConfig) return null;

  const { labelCol, primaryMetric, secondaryMetric, maxPrimary, maxSecondary } = chartConfig;
  const displayRows = rows.slice(0, 12);

  return (
    <div className="bg-zinc-900/40 border border-zinc-800/70 rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[11px] font-bold text-zinc-400 flex items-center tracking-widest uppercase">
          <svg
            className="w-4 h-4 mr-2 text-cyan-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          {secondaryMetric
            ? `${primaryMetric.replace(/_/g, ' ')} vs ${secondaryMetric.replace(/_/g, ' ')}`
            : `${primaryMetric.replace(/_/g, ' ')} Distribution`}
        </h3>
        {secondaryMetric && (
          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5 text-cyan-300">
              <span className="w-2.5 h-2.5 rounded-sm bg-cyan-400 inline-block"></span>
              {primaryMetric.replace(/_/g, ' ')}
            </span>
            <span className="flex items-center gap-1.5 text-emerald-300">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400 inline-block"></span>
              {secondaryMetric.replace(/_/g, ' ')}
            </span>
          </div>
        )}
      </div>

      <div className="space-y-3.5 max-h-[320px] overflow-y-auto pr-2 custom-scrollbar">
        {displayRows.map((row, idx) => {
          const val1 = Number(row[primaryMetric]) || 0;
          const pct1 = Math.max((val1 / maxPrimary) * 100, 2);
          const val2 = secondaryMetric ? Number(row[secondaryMetric]) || 0 : 0;
          const pct2 = secondaryMetric ? Math.max((val2 / maxSecondary) * 100, 2) : 0;

          return (
            <div key={idx} className="group/bar">
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="truncate max-w-[60%] font-medium text-zinc-200 group-hover/bar:text-cyan-300 transition-colors">
                  {String(row[labelCol])}
                </span>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-cyan-300">{val1.toLocaleString('en-IN')}</span>
                  {secondaryMetric && (
                    <span className="text-emerald-300 border-l border-zinc-700 pl-2">
                      {val2.toLocaleString('en-IN')}
                    </span>
                  )}
                </div>
              </div>
              <div className="space-y-1">
                <div className="h-2 w-full bg-[#121215] rounded-full overflow-hidden border border-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500/80 to-cyan-400 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${pct1}%` }}
                  />
                </div>
                {secondaryMetric && (
                  <div className="h-1.5 w-full bg-[#121215] rounded-full overflow-hidden border border-white/5">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500/80 to-emerald-400 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${pct2}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
