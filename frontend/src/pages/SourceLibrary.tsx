import React, { useEffect, useState } from 'react';
import { getSources, deleteSource } from '../services/api';
import type { SourceMetadata } from '../types';
import { MultiUpload } from '../components/workspace/MultiUpload';

export const SourceLibrary: React.FC = () => {
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSources = async () => {
    try {
      const data = await getSources();
      setSources(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteSource(id);
      setSources(sources.filter(s => s.source_id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const formatSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let l = 0, n = bytes || 0;
    while(n >= 1024 && ++l) n = n/1024;
    return(n.toFixed(n < 10 && l > 0 ? 1 : 0) + ' ' + units[l]);
  };

  return (
    <div className="max-w-5xl mx-auto py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100 mb-2">Knowledge Base</h1>
        <p className="text-zinc-400">Upload and manage sources (Databases, PDFs, Documents) that the AI can query and synthesize.</p>
      </div>

      <div className="mb-12">
        <MultiUpload onUploadSuccess={() => loadSources()} />
      </div>

      <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-zinc-800/50 bg-zinc-900/80 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">Available Sources</h2>
          <span className="text-xs font-medium text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-md border border-cyan-500/20">{sources.length} sources</span>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-zinc-500">Loading sources...</div>
        ) : sources.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-16 h-16 bg-zinc-800/50 rounded-full flex items-center justify-center text-zinc-500 mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            </div>
            <p className="text-zinc-400 font-medium mb-1">No sources uploaded yet</p>
            <p className="text-zinc-500 text-sm">Upload a database or document above to begin.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-zinc-900/30 text-zinc-500 text-xs uppercase font-semibold tracking-wider">
                  <th className="px-6 py-4">Name</th>
                  <th className="px-6 py-4">Type</th>
                  <th className="px-6 py-4">Size</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Uploaded</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {sources.map(source => (
                  <tr key={source.source_id} className="hover:bg-zinc-800/20 transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-zinc-200">
                      {source.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-400">
                      <span className="bg-zinc-800 text-zinc-300 px-2 py-1 rounded text-xs">
                        {source.detected_format.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-400 font-mono">
                      {formatSize(source.size_bytes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {source.status === 'failed' ? (
                        <div className="flex flex-col">
                          <span className="text-red-400 font-semibold uppercase text-xs">FAILED</span>
                          {source.error_message && (
                            <span className="text-red-500/70 text-[10px] truncate max-w-[150px]" title={source.error_message}>
                              {source.error_message}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-emerald-400 font-semibold uppercase text-xs">READY</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-500">
                      {new Date(source.uploaded_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <button 
                        onClick={() => handleDelete(source.source_id)}
                        className="text-zinc-500 hover:text-red-400 transition-colors p-2 hover:bg-red-500/10 rounded-lg"
                        title="Delete Source"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
