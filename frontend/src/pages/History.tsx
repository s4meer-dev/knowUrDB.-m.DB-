import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory, getHistoryItem, deleteHistoryItem, clearHistory } from '../services/api';
import type { HistoryItem as HistoryItemType } from '../types';
import { HistoryList } from '../components/history/HistoryList';
import { HistoryDetail } from '../components/history/HistoryDetail';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';

export const History: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<HistoryItemType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  const [selectedItem, setSelectedItem] = useState<HistoryItemType | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [clearingAll, setClearingAll] = useState(false);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(false);
      const data = await getHistory();
      setItems(data.items);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleItemClick = async (id: string) => {
    try {
      const data = await getHistoryItem(id);
      setSelectedItem(data);
    } catch (e) {
      alert("Failed to load query details.");
    }
  };

  const handleRunAgain = (question: string) => {
    // We navigate to workspace and pass the question via state or just simple local storage
    // But since they are separated by router, the simplest is to navigate and use a query param
    // Since we don't have query params setup, we'll just navigate, but a robust app would use location.state
    navigate('/', { state: { initialQuestion: question } });
  };

  const handleDelete = async (id: string) => {
    try {
      setDeletingId(id);
      await deleteHistoryItem(id);
      setItems(items.filter(item => item.id !== id));
      if (selectedItem?.id === id) {
        setSelectedItem(null);
      }
    } catch (e) {
      alert("Failed to delete record.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to delete all query history? This cannot be undone.")) return;
    
    try {
      setClearingAll(true);
      await clearHistory();
      setItems([]);
    } catch (e) {
      alert("Failed to clear history.");
    } finally {
      setClearingAll(false);
    }
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <ErrorState 
          title="Failed to load history" 
          message="There was a problem communicating with the server."
          onRetry={fetchHistory}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto space-y-6 animate-fade-in pt-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-3xl font-bold text-zinc-900 tracking-tight">Query History</h2>
          <p className="text-zinc-500 mt-2 text-lg">Review your past database questions and results.</p>
        </div>
        
        {items.length > 0 && !loading && (
          <button
            onClick={handleClearAll}
            disabled={clearingAll}
            className="text-red-500 hover:text-red-700 hover:bg-red-50 px-4 py-2 rounded-xl transition-all text-sm font-semibold disabled:opacity-50"
          >
            {clearingAll ? 'Clearing...' : 'Clear All'}
          </button>
        )}
      </div>

      <div className="flex-1">
        {!loading && items.length === 0 ? (
          <div className="mt-12">
            <EmptyState 
              title="No history yet" 
              message="Your recent database queries will appear here." 
              icon={
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              }
              action={
                <button 
                  onClick={() => navigate('/')}
                  className="mt-4 text-zinc-900 bg-zinc-100 hover:bg-zinc-200 px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  Start exploring your data &rarr;
                </button>
              }
            />
          </div>
        ) : (
          <HistoryList 
            items={items} 
            isLoading={loading} 
            onItemClick={handleItemClick} 
          />
        )}
      </div>

      {selectedItem && (
        <HistoryDetail 
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onRunAgain={handleRunAgain}
          onDelete={handleDelete}
          isDeleting={deletingId === selectedItem.id}
        />
      )}
    </div>
  );
};

