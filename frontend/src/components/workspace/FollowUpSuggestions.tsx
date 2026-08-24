import React from 'react';

interface FollowUpSuggestionsProps {
  suggestions?: string[];
  onSelect: (question: string) => void;
  disabled: boolean;
}

export const FollowUpSuggestions: React.FC<FollowUpSuggestionsProps> = ({ 
  suggestions, 
  onSelect,
  disabled
}) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="p-4 border-b border-gray-200 bg-white">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Follow-up questions
      </h3>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(s)}
            disabled={disabled}
            className="text-sm bg-gray-50 text-indigo-600 border border-indigo-100 hover:bg-indigo-50 hover:border-indigo-300 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50 text-left flex items-center"
          >
            <svg className="w-3.5 h-3.5 mr-1.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
};
