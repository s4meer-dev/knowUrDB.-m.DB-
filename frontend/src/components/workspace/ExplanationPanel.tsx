import React from 'react';

interface ExplanationPanelProps {
  explanation?: string;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) return null;

  return (
    <div className="bg-indigo-50 border-b border-indigo-100 p-4">
      <h3 className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-2 flex items-center">
        <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        How KnowUrDB answered this
      </h3>
      <p className="text-sm text-indigo-900 leading-relaxed">
        {explanation}
      </p>
    </div>
  );
};
