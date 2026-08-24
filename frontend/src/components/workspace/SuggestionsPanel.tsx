import React, { useEffect, useState } from 'react';
import { getSuggestions } from '../../services/api';
import type { Suggestion } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface SuggestionsPanelProps {
  onSelectSuggestion: (question: string) => void;
  disabled: boolean;
}

export const SuggestionsPanel: React.FC<SuggestionsPanelProps> = ({ 
  onSelectSuggestion, 
  disabled 
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      setError(false);
      const data = await getSuggestions();
      setSuggestions(data.suggestions);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 min-h-[120px] flex items-center justify-center">
        <LoadingSpinner size="sm" text="Loading suggestions..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 text-center">
        <p className="text-sm text-gray-500 mb-2">Could not load suggestions.</p>
        <button 
          onClick={fetchSuggestions}
          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
        >
          Try again
        </button>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider flex items-center">
          <svg className="w-4 h-4 mr-1 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          Suggested Questions
        </h3>
        <button 
          onClick={fetchSuggestions}
          className="text-gray-400 hover:text-indigo-600 p-1 rounded-md transition-colors"
          title="Refresh suggestions"
          disabled={disabled}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </button>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSelectSuggestion(s.question)}
            disabled={disabled}
            className="text-sm bg-gray-50 text-gray-700 border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50 text-left flex-grow md:flex-grow-0"
          >
            {s.question}
          </button>
        ))}
      </div>
    </div>
  );
};
