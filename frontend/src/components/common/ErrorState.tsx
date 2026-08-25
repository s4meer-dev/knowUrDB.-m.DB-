import React from 'react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  type?: 'error' | 'info';
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title = "Something went wrong", 
  message, 
  onRetry,
  type = 'error'
}) => {
  const isInfo = type === 'info' || message.includes('confidently interpret') || message.includes('designed to answer');
  
  const bgClass = isInfo ? "bg-cyan-900/10 border-cyan-800/30 text-cyan-400" : "bg-red-900/10 border-red-800/30 text-red-400";
  const iconBgClass = isInfo ? "bg-cyan-500/20" : "bg-red-500/20";
  const iconClass = isInfo ? "text-cyan-400" : "text-red-400";
  const buttonClass = isInfo ? "bg-cyan-600 hover:bg-cyan-500" : "bg-red-600 hover:bg-red-500";
  
  const displayTitle = isInfo ? "Clarification Needed" : title;

  return (
    <div className={`${bgClass} border p-6 rounded-xl flex flex-col items-center justify-center text-center max-w-lg mx-auto backdrop-blur-sm shadow-lg`}>
      <div className={`${iconBgClass} p-3 rounded-full mb-4 shadow-[inset_0_0_10px_rgba(0,0,0,0.1)]`}>
        {isInfo ? (
            <svg className={`w-8 h-8 ${iconClass}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        ) : (
            <svg className={`w-8 h-8 ${iconClass}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        )}
      </div>
      <h3 className="font-bold text-lg mb-2 text-zinc-100">{displayTitle}</h3>
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
