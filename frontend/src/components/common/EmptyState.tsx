import React from 'react';

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, icon, action }) => {
  return (
    <div className="h-full flex flex-col items-center justify-center text-zinc-500 p-12 text-center border-2 border-dashed border-zinc-800/80 rounded-xl bg-zinc-900/30 backdrop-blur-sm">
      <div className="text-zinc-700 mb-4">
        {icon || (
          <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
        )}
      </div>
      <h3 className="text-xl font-semibold text-zinc-300 mb-2">{title}</h3>
      <p className="max-w-md mx-auto mb-6 font-medium text-zinc-500">{message}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
