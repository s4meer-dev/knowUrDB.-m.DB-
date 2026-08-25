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
    <aside className="w-64 bg-[#09090b]/80 backdrop-blur-xl border-r border-zinc-800/50 flex-shrink-0 hidden md:flex flex-col h-[calc(100vh-65px)] sticky top-[65px]">
      <nav className="flex-1 py-8 px-4 space-y-1.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => 
              `flex items-center px-4 py-3 rounded-xl transition-all font-medium text-sm border
              ${isActive 
                ? 'bg-zinc-900 border-zinc-700/50 shadow-[0_0_15px_rgba(34,211,238,0.05)] text-cyan-400' 
                : 'border-transparent text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/50'}`
            }
          >
            <div className={`mr-3 transition-colors ${location.pathname === item.to ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-zinc-300'}`}>
              {item.icon}
            </div>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};
