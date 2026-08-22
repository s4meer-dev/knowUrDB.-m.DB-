import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import * as api from './services/api';

vi.mock('./services/api', () => ({
  checkHealth: vi.fn(),
  queryDatabase: vi.fn(),
}));

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially for backend check', () => {
    vi.mocked(api.checkHealth).mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<App />);
    expect(screen.getByText('Checking backend...')).toBeInTheDocument();
  });

  it('renders connected state on success', async () => {
    vi.mocked(api.checkHealth).mockResolvedValue({
      status: 'healthy',
      service: 'knowUrDB-backend',
      version: '0.1.0',
    });
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('renders error state on failure', async () => {
    vi.mocked(api.checkHealth).mockRejectedValue(new Error('Network Error'));
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });

  it('renders query input and buttons', () => {
    vi.mocked(api.checkHealth).mockResolvedValue({
      status: 'healthy',
      service: 'knowUrDB-backend',
      version: '0.1.0',
    });
    render(<App />);
    
    expect(screen.getByPlaceholderText('Ask a question about the university database...')).toBeInTheDocument();
    expect(screen.getByText('Ask Database')).toBeInTheDocument();
    expect(screen.getByText('How many students are in the database?')).toBeInTheDocument();
  });

  it('handles successful query', async () => {
    vi.mocked(api.checkHealth).mockResolvedValue({
      status: 'healthy',
      service: 'knowUrDB-backend',
      version: '0.1.0',
    });
    
    vi.mocked(api.queryDatabase).mockResolvedValue({
      question: 'How many students?',
      generated_sql: 'SELECT COUNT(*) FROM students;',
      columns: ['COUNT(*)'],
      rows: [{'COUNT(*)': 4000}],
      row_count: 1,
      execution_time_ms: 1.5,
      status: 'success'
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
    
    const input = screen.getByPlaceholderText('Ask a question about the university database...');
    fireEvent.change(input, { target: { value: 'How many students?' } });
    
    const askButton = screen.getByText('Ask Database');
    fireEvent.click(askButton);
    
    await waitFor(() => {
      expect(screen.getByText('Query Result')).toBeInTheDocument();
      expect(screen.getByText('1 row returned in 1.5ms')).toBeInTheDocument();
      expect(screen.getByText('4000')).toBeInTheDocument();
    });
  });

  it('handles query error', async () => {
    vi.mocked(api.checkHealth).mockResolvedValue({
      status: 'healthy',
      service: 'knowUrDB-backend',
      version: '0.1.0',
    });
    
    vi.mocked(api.queryDatabase).mockRejectedValue(new Error('Syntax Error'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
    
    const input = screen.getByPlaceholderText('Ask a question about the university database...');
    fireEvent.change(input, { target: { value: 'Drop everything' } });
    
    const askButton = screen.getByText('Ask Database');
    fireEvent.click(askButton);
    
    await waitFor(() => {
      expect(screen.getByText('Query Error')).toBeInTheDocument();
      expect(screen.getByText('Syntax Error')).toBeInTheDocument();
    });
  });
});
