import React from 'react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  type?: 'error' | 'info';
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title, 
  message, 
  onRetry,
  type = 'error'
}) => {
  const isInfo = type === 'info' || message.includes('confidently interpret') || message.includes('designed to answer') || message.includes('find relevant data') || message.includes('There is no dataset');
  
  if (isInfo) {
    const displayTitle = title !== undefined ? title : "AI Response";
    return (
      <div className="bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border border-indigo-500/30 p-8 rounded-2xl flex flex-col items-center justify-center text-center max-w-2xl mx-auto backdrop-blur-md shadow-2xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 to-purple-500/10 opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>
        <div className="bg-indigo-500/20 p-4 rounded-full mb-6 shadow-[0_0_20px_rgba(99,102,241,0.2)] relative z-10 animate-pulse">
            <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
        </div>
        {displayTitle && <h3 className="font-bold text-xl mb-3 text-indigo-100 relative z-10 tracking-tight">{displayTitle}</h3>}
        <p className="text-base text-indigo-200/80 mb-8 max-w-lg font-medium leading-relaxed relative z-10">{message}</p>
        {onRetry && (
          <button 
            onClick={onRetry}
            className="relative z-10 bg-indigo-600/80 hover:bg-indigo-500 text-white px-8 py-2.5 rounded-xl font-semibold transition-all shadow-lg hover:shadow-indigo-500/25 hover:scale-105 active:scale-95 border border-indigo-500/50"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  const bgClass = "bg-red-900/10 border-red-800/30 text-red-400";
  const iconBgClass = "bg-red-500/20";
  const iconClass = "text-red-400";
  const buttonClass = "bg-red-600 hover:bg-red-500";
  
  return (
    <div className={`${bgClass} border p-6 rounded-xl flex flex-col items-center justify-center text-center max-w-lg mx-auto backdrop-blur-sm shadow-lg`}>
      <div className={`${iconBgClass} p-3 rounded-full mb-4 shadow-[inset_0_0_10px_rgba(0,0,0,0.1)]`}>
          <svg className={`w-8 h-8 ${iconClass}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
      </div>
      <h3 className="font-bold text-lg mb-2 text-zinc-100">{title !== undefined ? title : "Something went wrong"}</h3>
      <p className="text-sm mb-6 max-w-md font-medium">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className={`${buttonClass} text-white px-6 py-2.5 rounded-lg font-semibold transition-all shadow-md hover:scale-105 active:scale-95`}
        >
          Try Again
        </button>
      )}
    </div>
  );
};
