import React, { useRef, useEffect } from 'react';

interface QueryInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled
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
    <div className="bg-white rounded-2xl shadow-sm border border-zinc-200 p-2 relative transition-all focus-within:ring-4 focus-within:ring-zinc-100 focus-within:border-zinc-300">
      <div className="flex flex-col relative">
        <textarea
          ref={textareaRef}
          className="w-full bg-transparent border-none rounded-xl p-4 pr-16 text-zinc-800 placeholder-zinc-400 focus:ring-0 focus:outline-none resize-none min-h-[100px] text-lg font-medium leading-relaxed disabled:opacity-50"
          placeholder="Ask anything about your database..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          rows={1}
          style={{ paddingBottom: '3.5rem' }}
        />
        
        <div className="absolute bottom-2 right-2 flex items-center justify-end">
          <button
            onClick={onSubmit}
            disabled={!value.trim() || disabled || isLoading}
            className={`flex items-center justify-center p-3 rounded-xl transition-all ${
              value.trim() && !disabled && !isLoading
                ? 'bg-zinc-900 text-white shadow-md hover:bg-zinc-800 hover:scale-105 active:scale-95'
                : 'bg-zinc-100 text-zinc-400 cursor-not-allowed'
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
  );
};
