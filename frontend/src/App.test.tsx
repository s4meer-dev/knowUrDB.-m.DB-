import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';
import * as api from './services/api';

vi.mock('./services/api', () => ({
  checkHealth: vi.fn(),
}));

describe('App', () => {
  it('renders loading state initially', () => {
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
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });

  it('renders error state on failure', async () => {
    vi.mocked(api.checkHealth).mockRejectedValue(new Error('Network Error'));
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByText('Unable to reach the backend API.')).toBeInTheDocument();
    });
  });
});
