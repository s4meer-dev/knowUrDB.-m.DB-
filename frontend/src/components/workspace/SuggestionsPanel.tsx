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
    <div className="w-full">
      <div className="flex flex-wrap items-center justify-center gap-2">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSelectSuggestion(s.question)}
            disabled={disabled}
            className="text-sm font-medium bg-white text-zinc-600 border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 hover:text-zinc-900 px-4 py-2 rounded-xl transition-all disabled:opacity-50 shadow-sm"
          >
            {s.question}
          </button>
        ))}
      </div>
    </div>
  );
};
