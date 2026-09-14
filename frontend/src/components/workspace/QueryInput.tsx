import React, { useRef, useEffect } from 'react';
import type { SourceMetadata } from '../../types';
import BorderGlow from '../BorderGlow/BorderGlow';

interface QueryInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled: boolean;
  sources?: SourceMetadata[];
  selectedSourceId?: string;
  onSourceChange?: (sourceId: string) => void;
  loadingSources?: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled,
  sources = [],
  selectedSourceId = 'all',
  onSourceChange = () => {},
  loadingSources = false
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled && !isLoading) {
        onSubmit();
      }
    }
  };

  return (
    <BorderGlow
      className="shadow-lg w-full"
      edgeSensitivity={4}
      glowColor="40 80 80"
      backgroundColor="#18181b"
      borderRadius={16}
      glowRadius={10}
      glowIntensity={1}
      coneSpread={3}
      animated={true}
      fillOpacity={0.02}
      colors={['#a855f7', '#22d3ee', '#3b82f6']}
    >
      <div className="flex flex-col p-2 w-full h-full relative">
        <div className="flex items-center px-4 pt-2 pb-1 border-b border-zinc-800/50 mb-1">
          <label htmlFor="source-selector" className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mr-3">
            Database / Source
          </label>
          <select
            id="source-selector"
            value={selectedSourceId}
            onChange={(e) => onSourceChange(e.target.value)}
            disabled={loadingSources || disabled || isLoading}
            className="bg-transparent text-sm font-medium text-cyan-400 focus:outline-none focus:ring-0 hover:text-cyan-300 transition-colors cursor-pointer disabled:opacity-50 min-w-[150px]"
          >
            <option value="all" className="bg-zinc-900 text-zinc-100">All Sources</option>
            {sources.map(s => (
              <option key={s.source_id} value={s.source_id} className="bg-zinc-900 text-zinc-100">
                {s.name} {s.record_count ? `(${s.record_count.toLocaleString()} rows)` : ''}
              </option>
            ))}
          </select>
          {loadingSources && (
            <div className="ml-2 w-3 h-3 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
          )}
        </div>

        <div className="flex flex-col relative">
          <textarea
            ref={textareaRef}
            className="w-full bg-transparent border-none rounded-xl p-4 pr-16 text-zinc-100 placeholder-zinc-500 focus:ring-0 focus:outline-none resize-none overflow-hidden min-h-[80px] text-lg font-medium leading-relaxed disabled:opacity-50"
            placeholder="Ask anything about your database..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            rows={1}
            style={{ paddingBottom: '3.5rem', outline: 'none' }}
          />
          
          <div className="absolute bottom-2 right-2 flex items-center justify-end">
            <button
              onClick={onSubmit}
              disabled={!value.trim() || disabled || isLoading}
              className={`flex items-center justify-center p-3 rounded-xl transition-all ${
                value.trim() && !disabled && !isLoading
                  ? 'bg-cyan-500 text-zinc-950 shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:bg-cyan-400 hover:scale-105 active:scale-95'
                  : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
              }`}
              title="Send Query (Enter)"
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-5 h-5 translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </BorderGlow>
  );
};
