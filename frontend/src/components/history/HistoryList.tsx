import React from 'react';
import type { HistoryItem as HistoryItemType } from '../../types';
import { HistoryItem } from './HistoryItem';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface HistoryListProps {
  items: HistoryItemType[];
  isLoading: boolean;
  onItemClick: (id: string) => void;
}

export const HistoryList: React.FC<HistoryListProps> = ({ items, isLoading, onItemClick }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
        <LoadingSpinner text="Loading your history..." />
      </div>
    );
  }

  return (
    <div className="space-y-3 group">
      {items.map(item => (
        <HistoryItem 
          key={item.id} 
          item={item} 
          onClick={() => onItemClick(item.id)} 
        />
      ))}
    </div>
  );
};
