
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MultiUpload } from '../components/workspace/MultiUpload';
import * as api from '../services/api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API module
vi.mock('../services/api', () => ({
  uploadSource: vi.fn(),
}));

describe('MultiUpload Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const createMockFile = (name: string, type = 'text/csv') => {
    return new File(['dummy content'], name, { type });
  };

  it('adds files to the queue when selected', async () => {
    render(<MultiUpload onUploadSuccess={() => {}} />);
    
    const input = screen.getByLabelText(/Browse Files/i) as HTMLInputElement;
    const file1 = createMockFile('orders.csv');
    const file2 = createMockFile('customers.csv');
    
    fireEvent.change(input, { target: { files: [file1, file2] } });
    
    expect(screen.getByText(/Selected files \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByText('customers.csv')).toBeInTheDocument();
  });

  it('prevents adding duplicate filenames to the queue', async () => {
    render(<MultiUpload onUploadSuccess={() => {}} />);
    
    const input = screen.getByLabelText(/Browse Files/i) as HTMLInputElement;
    const file1 = createMockFile('orders.csv');
    
    // Add first time
    fireEvent.change(input, { target: { files: [file1] } });
    expect(screen.getByText(/Selected files \(1\)/i)).toBeInTheDocument();
    
    // Add second time (same name)
    const file2 = createMockFile('orders.csv');
    fireEvent.change(input, { target: { files: [file2] } });
    
    // Still 1 file
    expect(screen.getByText(/Selected files \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Some files were skipped/i)).toBeInTheDocument();
  });

  it('allows removing a file from the queue before uploading', async () => {
    render(<MultiUpload onUploadSuccess={() => {}} />);
    
    const input = screen.getByLabelText(/Browse Files/i) as HTMLInputElement;
    const file1 = createMockFile('orders.csv');
    const file2 = createMockFile('customers.csv');
    
    fireEvent.change(input, { target: { files: [file1, file2] } });
    
    const removeButtons = screen.getAllByTitle('Remove');
    expect(removeButtons).toHaveLength(2);
    
    // Remove the first one
    fireEvent.click(removeButtons[0]);
    
    expect(screen.getByText(/Selected files \(1\)/i)).toBeInTheDocument();
  });

  it('clears all files when Clear All is clicked', async () => {
    render(<MultiUpload onUploadSuccess={() => {}} />);
    
    const input = screen.getByLabelText(/Browse Files/i) as HTMLInputElement;
    const file1 = createMockFile('orders.csv');
    fireEvent.change(input, { target: { files: [file1] } });
    
    const clearButton = screen.getByText('Clear All');
    fireEvent.click(clearButton);
    
    expect(screen.queryByText(/Selected files/i)).not.toBeInTheDocument();
  });

  it('uploads files correctly and reports success/error', async () => {
    const mockOnSuccess = vi.fn();
    render(<MultiUpload onUploadSuccess={mockOnSuccess} />);
    
    // Setup API mock to succeed on first, fail on second
    (api.uploadSource as any)
      .mockResolvedValueOnce({ source_id: 'src_1', name: 'ok.csv' })
      .mockRejectedValueOnce({ response: { data: { detail: 'Upload failed' } } });

    const input = screen.getByLabelText(/Browse Files/i) as HTMLInputElement;
    const file1 = createMockFile('ok.csv');
    const file2 = createMockFile('fail.csv');
    
    fireEvent.change(input, { target: { files: [file1, file2] } });
    
    const uploadButton = screen.getByText('Upload All');
    fireEvent.click(uploadButton);
    
    // Wait for the upload queue to process
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });
    
    expect(mockOnSuccess).toHaveBeenCalledTimes(1);
  });
});
