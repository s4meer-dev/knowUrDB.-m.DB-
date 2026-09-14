import React, { useRef, useEffect } from 'react';
import type { SourceMetadata } from '../../types';
import BorderGlow from '../BorderGlow/BorderGlow';
import { CustomDropdown } from '../common/CustomDropdown';

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
      className="shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full transition-transform duration-300"
      edgeSensitivity={8}
      glowColor="40 80 80"
      backgroundColor="#09090b"
      borderRadius={24}
      glowRadius={12}
      glowIntensity={1.5}
      coneSpread={5}
      animated={true}
      fillOpacity={0.03}
      colors={['#06b6d4', '#8b5cf6', '#3b82f6']}
    >
      <div className="flex flex-col w-full h-full relative rounded-[24px] bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 backdrop-blur-2xl border border-white/[0.03] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]">
        {/* Aesthetic Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.04] bg-white/[0.01]">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,1)]"></span>
              </div>
              <label htmlFor="source-selector" className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] select-none">
                Database / Source
              </label>
            </div>
            <div className="h-4 w-px bg-zinc-800/80"></div>
            <CustomDropdown
              value={selectedSourceId}
              onChange={onSourceChange}
              disabled={loadingSources || disabled || isLoading}
              options={[
                { value: 'all', label: 'All Sources' },
                ...sources.map(s => ({
                  value: s.source_id,
                  label: s.name,
                  subLabel: s.record_count ? `${s.record_count.toLocaleString()} rows` : undefined
                }))
              ]}
              triggerClassName="bg-transparent text-sm font-semibold text-cyan-400 focus:outline-none hover:text-cyan-300 hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.5)] transition-all cursor-pointer disabled:opacity-50 min-w-[150px] flex items-center justify-between group"
              dropdownClassName="w-64 mt-3 -left-4"
            />
          </div>
          {loadingSources && (
            <div className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin shadow-[0_0_10px_rgba(34,211,238,0.2)]"></div>
          )}
        </div>

        {/* Text Input Area */}
        <div className="flex flex-col relative group">
          {/* Subtle gradient glow behind the text that appears on focus/hover */}
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/5 to-purple-500/0 opacity-0 group-focus-within:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
          
          <textarea
            ref={textareaRef}
            className="w-full bg-transparent border-none rounded-b-[24px] p-6 pr-20 text-zinc-100 placeholder-zinc-600 focus:ring-0 focus:outline-none resize-none overflow-hidden min-h-[100px] text-lg font-medium leading-relaxed disabled:opacity-50 relative z-10 transition-colors"
            placeholder="Ask anything about your database..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            rows={1}
            style={{ paddingBottom: '4.5rem', outline: 'none' }}
          />
          
          {/* Submit Button */}
          <div className="absolute bottom-4 right-4 flex items-center justify-end z-20">
            <button
              onClick={onSubmit}
              disabled={!value.trim() || disabled || isLoading}
              className={`relative flex items-center justify-center p-3.5 rounded-xl overflow-hidden transition-all duration-300 group ${
                value.trim() && !disabled && !isLoading
                  ? 'text-zinc-950 shadow-[0_0_20px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_rgba(34,211,238,0.6)] hover:scale-105 active:scale-95'
                  : 'bg-zinc-800/50 text-zinc-600 cursor-not-allowed border border-zinc-700/50'
              }`}
              title="Send Query (Enter)"
            >
              {/* Dynamic glowing background for active state */}
              {value.trim() && !disabled && !isLoading && (
                <>
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-400 to-blue-500 z-0"></div>
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] z-0"></div>
                </>
              )}
              
              <div className="relative z-10 flex items-center justify-center">
                {isLoading ? (
                  <svg className="animate-spin h-5 w-5 text-cyan-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5 translate-x-0.5 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                  </svg>
                )}
              </div>
            </button>
          </div>
        </div>
      </div>
    </BorderGlow>
  );
};
