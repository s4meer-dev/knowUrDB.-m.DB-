import React, { useState, useCallback } from 'react';
import { uploadSource } from '../../services/api';
import type { SourceMetadata } from '../../types';

interface MultiUploadProps {
  onUploadSuccess: (source: SourceMetadata) => void;
}

export const MultiUpload: React.FC<MultiUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<{name: string, status: 'uploading' | 'success' | 'error', error?: string}[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFiles = async (files: File[]) => {
    const newUploads = files.map(f => ({ name: f.name, status: 'uploading' as const }));
    setUploadingFiles(prev => [...newUploads, ...prev]);

    for (const file of files) {
      try {
        const result = await uploadSource(file);
        setUploadingFiles(prev => prev.map(u => u.name === file.name ? { ...u, status: 'success' } : u));
        onUploadSuccess(result);
      } catch (err: any) {
        setUploadingFiles(prev => prev.map(u => u.name === file.name ? { ...u, status: 'error', error: err.response?.data?.detail?.message || 'Failed' } : u));
      }
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(Array.from(e.target.files));
      e.target.value = ''; // Reset
    }
  };

  return (
    <div className="w-full">
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 ${
          isDragging 
            ? 'border-cyan-500 bg-cyan-500/10' 
            : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-800/50'
        }`}
      >
        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-4 text-cyan-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-zinc-300 font-medium mb-1">Drag and drop files here</p>
        <p className="text-zinc-500 text-sm mb-4">Supports SQLite, PDF, TXT, Markdown, CSV, Excel</p>
        
        <label className="cursor-pointer">
          <span className="px-4 py-2 rounded-lg bg-zinc-100 text-zinc-900 hover:bg-white font-medium text-sm transition-colors">
            Browse Files
          </span>
          <input 
            type="file" 
            className="hidden" 
            multiple 
            onChange={handleFileSelect}
            accept=".db,.sqlite,.sqlite3,.csv,.xlsx,.xls,.parquet,.duckdb,.pdf,.txt,.md"
          />
        </label>
      </div>

      {uploadingFiles.length > 0 && (
        <div className="mt-6 space-y-2">
          {uploadingFiles.map((file, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800/80">
              <div className="flex items-center gap-3 truncate">
                {file.status === 'uploading' && (
                  <div className="w-4 h-4 rounded-full border-2 border-cyan-500/30 border-t-cyan-500 animate-spin flex-shrink-0" />
                )}
                {file.status === 'success' && (
                  <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                )}
                {file.status === 'error' && (
                  <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                )}
                <span className="text-sm font-medium text-zinc-300 truncate">{file.name}</span>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-md ${
                file.status === 'uploading' ? 'bg-cyan-500/10 text-cyan-400' :
                file.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                'bg-red-500/10 text-red-400'
              }`}>
                {file.status === 'uploading' ? 'Processing...' : 
                 file.status === 'success' ? 'Ready' : 'Failed'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
