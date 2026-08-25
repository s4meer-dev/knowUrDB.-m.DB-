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
      <div className="bg-[#09090b]/50 backdrop-blur-sm rounded-xl border border-zinc-800/50 p-4 min-h-[120px] flex items-center justify-center">
        <LoadingSpinner size="sm" text="Loading suggestions..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#09090b]/50 backdrop-blur-sm rounded-xl border border-zinc-800/50 p-4 text-center">
        <p className="text-sm text-zinc-500 mb-2">Could not load suggestions.</p>
        <button 
          onClick={fetchSuggestions}
          className="text-cyan-500 hover:text-cyan-400 text-sm font-medium transition-colors"
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
      <div className="flex flex-wrap items-center justify-center gap-3">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSelectSuggestion(s.question)}
            disabled={disabled}
            className="text-sm font-medium bg-zinc-900/50 backdrop-blur-sm text-zinc-400 border border-zinc-800/80 hover:border-cyan-500/30 hover:text-cyan-400 hover:bg-cyan-500/5 px-4 py-2.5 rounded-full transition-all disabled:opacity-50 shadow-sm"
          >
            {s.question}
          </button>
        ))}
      </div>
    </div>
  );
};
