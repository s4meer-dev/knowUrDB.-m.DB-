import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import * as api from './services/api';

vi.mock('./services/api', () => ({
  checkHealth: vi.fn(),
  checkAiStatus: vi.fn(),
  queryDatabase: vi.fn(),
  getSuggestions: vi.fn(),
  getHistory: vi.fn(),
  getSchema: vi.fn()
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (api.checkHealth as any).mockResolvedValue({ status: 'ok' });
    (api.checkAiStatus as any).mockResolvedValue({ status: 'ready', configured: true });
    (api.getSuggestions as any).mockResolvedValue({ suggestions: [] });
  });

  it('renders the application shell and checks health', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    // Header title
    expect(screen.getByText('KnowUrDB')).toBeInTheDocument();
    
    // Check if connected state is shown after mock resolves
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('Ready')).toBeInTheDocument();
    });
  });
});
