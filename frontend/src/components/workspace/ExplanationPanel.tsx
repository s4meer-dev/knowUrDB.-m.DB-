import React from 'react';

interface ExplanationPanelProps {
  explanation?: string;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) return null;

  return (
    <div className="bg-cyan-500/5 border-b border-cyan-500/10 p-5">
      <h3 className="text-[11px] font-semibold text-cyan-500 uppercase tracking-wider mb-2 flex items-center">
        <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        AI Explanation
      </h3>
      <p className="text-sm text-cyan-100/80 leading-relaxed font-medium">
        {explanation}
      </p>
    </div>
  );
};
