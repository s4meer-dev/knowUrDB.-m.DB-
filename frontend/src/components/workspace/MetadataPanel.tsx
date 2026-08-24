import React from 'react';

interface MetadataPanelProps {
  rowCount: number;
  executionTimeMs: number;
  querySource?: string;
}

export const MetadataPanel: React.FC<MetadataPanelProps> = ({ 
  rowCount, 
  executionTimeMs, 
  querySource 
}) => {
  const getSourceDisplay = (source?: string) => {
    if (source === 'ai') return 'AI generated';
    if (source === 'fallback') return 'Fallback logic';
    return source || 'System';
  };

  return (
    <div className="bg-gray-50 border-t border-gray-200 p-3 px-6 flex flex-wrap gap-6 text-xs text-gray-500 justify-end">
      <div className="flex items-center">
        <svg className="w-3.5 h-3.5 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
        </svg>
        {rowCount} row{rowCount !== 1 ? 's' : ''}
      </div>
      
      <div className="flex items-center">
        <svg className="w-3.5 h-3.5 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        Executed in {executionTimeMs} ms
      </div>

      {querySource && (
        <div className="flex items-center">
          <svg className="w-3.5 h-3.5 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
          </svg>
          {getSourceDisplay(querySource)}
        </div>
      )}
    </div>
  );
};
