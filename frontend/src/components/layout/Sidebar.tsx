import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const navItems = [
    {
      to: '/',
      label: 'Query Workspace',
      icon: (
        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
        </svg>
      )
    },
    {
      to: '/history',
      label: 'Query History',
      icon: (
        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      )
    },
    {
      to: '/schema',
      label: 'Schema Explorer',
      icon: (
        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
        </svg>
      )
    }
  ];

  return (
    <aside className="w-64 bg-white/50 backdrop-blur-sm border-r border-zinc-200 flex-shrink-0 hidden md:flex flex-col h-[calc(100vh-65px)] sticky top-[65px]">
      <nav className="flex-1 py-6 px-4 space-y-1.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => 
              `flex items-center px-4 py-2.5 rounded-lg transition-all font-medium text-sm border
              ${isActive 
                ? 'bg-white border-zinc-200/60 shadow-sm text-zinc-900' 
                : 'border-transparent text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100/50'}`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-zinc-200/50">
        <div className="bg-zinc-900 rounded-xl p-4 text-center group cursor-pointer transition-transform hover:scale-[1.02]">
          <div className="w-8 h-8 bg-zinc-800 text-zinc-300 rounded-lg flex items-center justify-center mx-auto mb-2 transition-colors group-hover:text-white group-hover:bg-zinc-700">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <p className="text-[11px] text-zinc-400 font-medium tracking-wide uppercase group-hover:text-zinc-300 transition-colors">Powered by AI</p>
        </div>
      </div>
    </aside>
  );
};
