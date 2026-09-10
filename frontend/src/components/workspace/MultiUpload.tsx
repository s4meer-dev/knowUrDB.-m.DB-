import React, { useState, useCallback } from 'react';
import { uploadBatchSources } from '../../services/api';
import type { SourceMetadata } from '../../types';

interface MultiUploadProps {
  onUploadSuccess: (source: SourceMetadata) => void;
}

type FileStatus = 'WAITING' | 'UPLOADING' | 'SUCCESS' | 'ERROR';

interface QueuedFile {
  id: string;
  file: File;
  status: FileStatus;
  error?: string;
}

export const MultiUpload: React.FC<MultiUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [errorToast, setErrorToast] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const addFilesToQueue = (files: File[]) => {
    setUploadQueue(prev => {
      const newFiles: QueuedFile[] = [];
      const existingNames = new Set(prev.map(q => q.file.name));
      let hasDuplicates = false;
      
      for (const file of files) {
        if (existingNames.has(file.name)) {
          hasDuplicates = true;
        } else {
          newFiles.push({
            id: Math.random().toString(36).substring(7),
            file,
            status: 'WAITING'
          });
        }
      }
      
      if (hasDuplicates) {
        setErrorToast("Some files were skipped because they are already selected.");
        setTimeout(() => setErrorToast(null), 3000);
      }
      
      return [...prev, ...newFiles];
    });
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToQueue(Array.from(e.target.files));
      e.target.value = ''; // Reset for re-selection
    }
  };

  const removeFile = (id: string) => {
    if (isUploading) return;
    setUploadQueue(prev => prev.filter(q => q.id !== id));
  };
  
  const clearQueue = () => {
    if (isUploading) return;
    setUploadQueue([]);
  };

  const uploadAll = async () => {
    if (isUploading) return;
    
    // Find all waiting or errored files
    const toUpload = uploadQueue.filter(q => q.status === 'WAITING' || q.status === 'ERROR');
    if (toUpload.length === 0) return;
    
    setIsUploading(true);
    
    // Mark them as uploading
    setUploadQueue(prev => prev.map(q => 
      (q.status === 'WAITING' || q.status === 'ERROR') ? { ...q, status: 'UPLOADING', error: undefined } : q
    ));

    try {
      const filesToUpload = toUpload.map(q => q.file);
      const results = await uploadBatchSources(filesToUpload);
      
      setUploadQueue(prev => prev.map(q => {
        if (toUpload.some(t => t.id === q.id)) {
          return { ...q, status: 'SUCCESS' };
        }
        return q;
      }));
      
      results.forEach(res => onUploadSuccess(res));
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to upload batch';
      setUploadQueue(prev => prev.map(q => {
        if (toUpload.some(t => t.id === q.id)) {
          return { ...q, status: 'ERROR', error: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage) };
        }
        return q;
      }));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      {/* Upload Dropzone */}
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
        <p className="text-zinc-300 font-medium mb-1">Drop your data sources here</p>
        <p className="text-zinc-500 text-sm mb-4">CSV • JSON • SQL • XLSX • PDF</p>
        
        <label className={`cursor-pointer ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}>
          <span className="px-4 py-2 rounded-lg bg-cyan-500 text-zinc-900 hover:bg-cyan-400 font-medium text-sm transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)]">
            Browse Files
          </span>
          <input 
            type="file" 
            className="hidden" 
            multiple 
            onChange={handleFileSelect}
            accept=".db,.sqlite,.sqlite3,.csv,.xlsx,.xls,.parquet,.duckdb,.pdf,.txt,.md,.json"
            disabled={isUploading}
          />
        </label>
        <p className="text-zinc-500 text-xs mt-4">Multiple files supported</p>
      </div>

      {errorToast && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium flex items-center">
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {errorToast}
        </div>
      )}

      {/* Upload Queue */}
      {uploadQueue.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-zinc-300 font-medium text-sm">Selected files ({uploadQueue.length})</h3>
            <div className="flex gap-3">
              <button 
                onClick={clearQueue}
                disabled={isUploading}
                className="text-xs font-medium text-zinc-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Clear All
              </button>
              <button
                onClick={uploadAll}
                disabled={isUploading || uploadQueue.every(q => q.status === 'SUCCESS')}
                className="text-xs font-medium px-3 py-1.5 rounded-md bg-zinc-800 text-white hover:bg-zinc-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Uploading...' : 'Upload All'}
              </button>
            </div>
          </div>
          
          <div className="space-y-2">
            {uploadQueue.map((q) => (
              <div key={q.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800/80">
                <div className="flex items-center gap-3 truncate max-w-[70%]">
                  {q.status === 'WAITING' && (
                    <svg className="w-4 h-4 text-zinc-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  )}
                  {q.status === 'UPLOADING' && (
                    <div className="w-4 h-4 rounded-full border-2 border-cyan-500/30 border-t-cyan-500 animate-spin flex-shrink-0" />
                  )}
                  {q.status === 'SUCCESS' && (
                    <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                  )}
                  {q.status === 'ERROR' && (
                    <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  )}
                  <div className="flex flex-col truncate">
                    <span className="text-sm font-medium text-zinc-300 truncate" title={q.file.name}>{q.file.name}</span>
                    {q.error && <span className="text-xs text-red-400 truncate" title={q.error}>{q.error}</span>}
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium px-2 py-1 rounded-md ${
                    q.status === 'WAITING' ? 'bg-zinc-800 text-zinc-400' :
                    q.status === 'UPLOADING' ? 'bg-cyan-500/10 text-cyan-400' :
                    q.status === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-400' :
                    'bg-red-500/10 text-red-400'
                  }`}>
                    {q.status === 'WAITING' ? 'Ready' :
                     q.status === 'UPLOADING' ? 'Uploading...' : 
                     q.status === 'SUCCESS' ? 'Success' : 'Failed'}
                  </span>
                  
                  {q.status === 'WAITING' && (
                    <button 
                      onClick={() => removeFile(q.id)}
                      disabled={isUploading}
                      className="p-1 text-zinc-500 hover:text-red-400 transition-colors disabled:opacity-50"
                      title="Remove"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                  )}
                  {q.status === 'ERROR' && !isUploading && (
                     <button 
                       onClick={() => uploadAll()}
                       className="p-1 text-zinc-500 hover:text-cyan-400 transition-colors"
                       title="Retry"
                     >
                       <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                     </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
