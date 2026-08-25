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
  
  const bgClass = isInfo ? "bg-blue-50 border-blue-200 text-blue-800" : "bg-red-50 border-red-200 text-red-700";
  const iconBgClass = isInfo ? "bg-blue-100" : "bg-red-100";
  const iconClass = isInfo ? "text-blue-600" : "text-red-600";
  const buttonClass = isInfo ? "bg-blue-600 hover:bg-blue-700" : "bg-red-600 hover:bg-red-700";
  
  const displayTitle = isInfo ? "Clarification Needed" : title;

  return (
    <div className={`${bgClass} border p-6 rounded-xl flex flex-col items-center justify-center text-center max-w-lg mx-auto`}>
      <div className={`${iconBgClass} p-3 rounded-full mb-4`}>
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
      <h3 className="font-bold text-lg mb-2">{displayTitle}</h3>
      <p className="text-sm mb-6 max-w-md">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className={`${buttonClass} text-white px-6 py-2 rounded-lg font-medium transition-colors`}
        >
          Try Again
        </button>
      )}
    </div>
  );
};
