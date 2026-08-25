import axios from 'axios';
import type { 
  HealthResponse, 
  AiStatusResponse,
  QueryRequest, 
  QueryResponse,
  HistoryListResponse,
  HistoryItem,
  SuggestionsResponse,
  SchemaSummary,
  TableInfo,
  DatabaseSchema
} from '../types';

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

export const checkAiStatus = async (): Promise<AiStatusResponse> => {
  const response = await apiClient.get<AiStatusResponse>('/api/ai/status');
  return response.data;
};

export const queryDatabase = async (question: string): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/api/query', { question } as QueryRequest);
  return response.data;
};

export const getHistory = async (): Promise<HistoryListResponse> => {
  const response = await apiClient.get<HistoryItem[]>('/api/history');
  return { items: response.data, total: response.data.length };
};

export const getHistoryItem = async (queryId: string): Promise<HistoryItem> => {
  const response = await apiClient.get<HistoryItem>(`/api/history/${queryId}`);
  return response.data;
};

export const deleteHistoryItem = async (queryId: string): Promise<void> => {
  await apiClient.delete(`/api/history/${queryId}`);
};

export const clearHistory = async (): Promise<void> => {
  await apiClient.delete('/api/history');
};

export const getSuggestions = async (): Promise<SuggestionsResponse> => {
  const response = await apiClient.get<SuggestionsResponse>('/api/suggestions');
  return response.data;
};

export const getSchema = async (): Promise<DatabaseSchema> => {
  const response = await apiClient.get<DatabaseSchema>('/api/schema');
  return response.data;
};

export const getTableSchema = async (table: string): Promise<TableInfo> => {
  const response = await apiClient.get<TableInfo>(`/api/schema/${table}`);
  return response.data;
};
