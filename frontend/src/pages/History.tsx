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

  const handleRunAgain = (question: string, sourceId?: string) => {
    navigate('/', { state: { initialQuestion: question, sourceId: sourceId } });
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

  const successCount = items.filter(i => i.status === 'success').length;
  const errorCount = items.length - successCount;

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto space-y-8 animate-fade-in pt-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 bg-zinc-900/30 p-8 rounded-3xl border border-zinc-800/80 shadow-2xl relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-900/10 to-transparent pointer-events-none"></div>
        <div className="relative z-10">
          <div className="w-16 h-16 bg-zinc-900 border border-zinc-700/50 rounded-2xl flex items-center justify-center shadow-lg text-cyan-400 mb-6">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          </div>
          <h2 className="text-4xl font-bold text-zinc-100 tracking-tight">Query History</h2>
          <p className="text-zinc-400 mt-3 text-lg max-w-lg">Review and re-run your past database questions, analyses, and results.</p>
        </div>
        
        {items.length > 0 && !loading && (
          <div className="relative z-10 flex items-center gap-6">
            <div className="flex items-center gap-6 text-sm font-medium border-r border-zinc-800/80 pr-6">
              <div className="flex flex-col items-center">
                <span className="text-3xl font-bold text-zinc-100">{items.length}</span>
                <span className="text-xs uppercase tracking-wider text-zinc-500">Total</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-xl font-bold text-emerald-400">{successCount}</span>
                <span className="text-xs uppercase tracking-wider text-zinc-500">Success</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-xl font-bold text-red-400">{errorCount}</span>
                <span className="text-xs uppercase tracking-wider text-zinc-500">Failed</span>
              </div>
            </div>
            <button
              onClick={handleClearAll}
              disabled={clearingAll}
              className="text-red-400 border border-red-500/20 hover:bg-red-500/10 px-5 py-2.5 rounded-xl transition-all text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              {clearingAll ? 'Clearing...' : 'Clear All'}
            </button>
          </div>
        )}
      </div>

      <div className="flex-1">
        {!loading && items.length === 0 ? (
          <div className="mt-8 bg-zinc-900/30 border border-zinc-800/50 rounded-3xl p-12 shadow-xl">
            <EmptyState 
              title="No history yet" 
              message="Your recent database queries and analysis sessions will appear here." 
              icon={
                <svg className="w-16 h-16 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              }
              action={
                <button 
                  onClick={() => navigate('/')}
                  className="mt-6 text-zinc-950 bg-cyan-500 hover:bg-cyan-400 px-8 py-3 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:scale-105"
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
