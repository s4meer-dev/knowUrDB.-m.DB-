import React, { useState, useEffect } from 'react';

interface SqlPanelProps {
  sql: string;
}

export const SqlPanel: React.FC<SqlPanelProps> = ({ sql }) => {
  const [copied, setCopied] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setIsVisible(true));
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`bg-[#060608]/90 backdrop-blur-xl text-zinc-100 p-6 m-4 mt-0 border border-white/[0.08] rounded-2xl shadow-[inset_0_2px_20px_rgba(255,255,255,0.02),0_10px_40px_rgba(0,0,0,0.6)] transition-all duration-700 ease-out relative overflow-hidden group ring-1 ring-white/5 ${isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 -translate-y-4 scale-[0.98]'}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-transparent opacity-50 pointer-events-none"></div>
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-[100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out pointer-events-none"></div>
      
      <div className="flex justify-between items-center mb-4 relative z-10 border-b border-white/[0.05] pb-3">
        <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-[0.2em] flex items-center bg-black/40 px-3 py-1.5 rounded-lg border border-white/[0.05]">
          <div className="relative flex h-2 w-2 mr-2">
             <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
             <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,1)]"></span>
          </div>
          Generated SQL Code
        </span>
        <button
          onClick={handleCopy}
          className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-300 flex items-center border ${copied ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]' : 'bg-white/5 text-zinc-400 border-transparent hover:bg-cyan-500/20 hover:text-cyan-300 hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(34,211,238,0.2)]'}`}
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"></path>
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
              </svg>
              Copy Code
            </>
          )}
        </button>
      </div>
      <div className="overflow-x-auto relative z-10 bg-black/40 p-5 rounded-xl border border-white/[0.03] shadow-inner">
        <pre className="text-[14px] font-mono whitespace-pre-wrap leading-relaxed tracking-wide">
          <code className="text-cyan-300/90 drop-shadow-[0_0_8px_rgba(34,211,238,0.3)] font-medium">
            {sql.split('\n').map((line, i) => (
              <span key={i} className="block hover:bg-white/5 px-2 -mx-2 rounded transition-colors duration-200">
                {line}
              </span>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
};
