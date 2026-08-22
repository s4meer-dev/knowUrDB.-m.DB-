import axios from 'axios';
import type { HealthResponse, QueryRequest, QueryResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/api/health');
  return response.data;
};

export const queryDatabase = async (question: string): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/api/query', { question } as QueryRequest);
  return response.data;
};
