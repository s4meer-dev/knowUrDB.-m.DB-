import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col font-sans text-zinc-100 selection:bg-cyan-500/30">
      <Header />
      <div className="flex flex-1 overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-900/5 to-transparent pointer-events-none"></div>
        <Sidebar />
        <main className="flex-1 overflow-auto relative z-10">
          <div className="max-w-7xl mx-auto p-4 md:p-8 w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
