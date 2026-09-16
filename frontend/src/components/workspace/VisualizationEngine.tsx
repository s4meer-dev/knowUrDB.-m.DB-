import React, { useMemo } from 'react';

interface VisualizationEngineProps {
  columns: string[];
  rows: Record<string, any>[];
}

export const VisualizationEngine: React.FC<VisualizationEngineProps> = ({ columns, rows }) => {
  // Determine if we can chart this
  const chartConfig = useMemo(() => {
    if (rows.length === 0 || rows.length > 20) return null; // Too many rows for a simple bar chart
    if (columns.length !== 2) return null; // Needs exactly 2 columns for a basic chart

    const type1 = typeof rows[0][columns[0]];
    const type2 = typeof rows[0][columns[1]];

    let labelCol = '';
    let valueCol = '';

    if (type1 === 'string' && type2 === 'number') {
      labelCol = columns[0];
      valueCol = columns[1];
    } else if (type1 === 'number' && type2 === 'string') {
      labelCol = columns[1];
      valueCol = columns[0];
    } else {
      return null; // Cannot chart
    }

    const maxValue = Math.max(...rows.map(r => Number(r[valueCol]) || 0));

    return { labelCol, valueCol, maxValue };
  }, [columns, rows]);

  if (!chartConfig) return null;

  const { labelCol, valueCol, maxValue } = chartConfig;

  return (
    <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-xl p-6 mb-8 mt-2 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none transition-opacity opacity-50 group-hover:opacity-100"></div>
      <h3 className="text-[11px] font-bold text-zinc-400 mb-6 flex items-center tracking-widest uppercase">
        <svg className="w-4 h-4 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
        Data Distribution
      </h3>
      <div className="space-y-5 max-h-[350px] overflow-y-auto pr-3 custom-scrollbar relative z-10">
        {rows.map((row, idx) => {
          const val = Number(row[valueCol]) || 0;
          const percentage = maxValue > 0 ? (val / maxValue) * 100 : 0;
          return (
            <div key={idx} className="relative group/bar cursor-default">
              <div className="flex justify-between items-end text-sm mb-1.5 z-10 relative">
                <span className="truncate max-w-[70%] font-medium text-zinc-300 group-hover/bar:text-cyan-300 transition-colors drop-shadow-md">{String(row[labelCol])}</span>
                <span className="text-zinc-200 font-mono font-medium drop-shadow-md group-hover/bar:text-cyan-400 transition-colors">{val.toLocaleString()}</span>
              </div>
              <div className="h-2 w-full bg-[#121214] rounded-full overflow-hidden shadow-inner border border-white/5">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500/80 to-cyan-400 rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(34,211,238,0.3)] group-hover/bar:shadow-[0_0_15px_rgba(34,211,238,0.6)] group-hover/bar:from-cyan-400 group-hover/bar:to-cyan-300"
                  style={{ width: `${Math.max(percentage, 1)}%`, animationDelay: `${idx * 50}ms` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
