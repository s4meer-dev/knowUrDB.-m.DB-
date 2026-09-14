import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import VerticalDock, { type DockItemData } from '../VerticalDock/VerticalDock';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const items: DockItemData[] = [
    {
      label: 'Query Workspace',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
        </svg>
      ),
      onClick: () => navigate('/'),
      isActive: location.pathname === '/'
    },
    {
      label: 'Knowledge Base',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
        </svg>
      ),
      onClick: () => navigate('/sources'),
      isActive: location.pathname === '/sources'
    },
    {
      label: 'Query History',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      ),
      onClick: () => navigate('/history'),
      isActive: location.pathname === '/history'
    },
    {
      label: 'Schema Explorer',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
        </svg>
      ),
      onClick: () => navigate('/schema'),
      isActive: location.pathname === '/schema'
    }
  ];

  return (
    <aside className="w-[100px] bg-transparent flex-shrink-0 hidden md:flex flex-col items-center pt-8 h-full relative z-40">
      <VerticalDock 
        items={items} 
        magnification={75}
        baseItemSize={50}
        distance={150}
      />
    </aside>
  );
};
