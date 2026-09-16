import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

interface ExplanationPanelProps {
  explanation?: string;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (explanation) {
      requestAnimationFrame(() => setIsVisible(true));
    }
  }, [explanation]);

  if (!explanation) return null;

  return (
    <div className={`bg-gradient-to-r from-cyan-950/40 via-cyan-900/10 to-transparent border-l-4 border-cyan-500/80 p-6 m-4 mt-2 rounded-r-xl shadow-[0_8px_30px_rgba(34,211,238,0.05)] transition-all duration-700 ease-out transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
      <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4 flex items-center drop-shadow-[0_0_12px_rgba(34,211,238,0.5)]">
        <svg className="w-5 h-5 mr-2 animate-pulse text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        AI Explanation
      </h3>
      <div className="text-[15px] text-cyan-50/95 leading-relaxed font-medium tracking-wide prose prose-invert prose-cyan max-w-none prose-p:leading-relaxed prose-li:my-1 prose-strong:text-white prose-strong:font-bold prose-ul:list-disc prose-ul:ml-4 prose-ol:list-decimal prose-ol:ml-4">
        <ReactMarkdown>{explanation}</ReactMarkdown>
      </div>
    </div>
  );
};
