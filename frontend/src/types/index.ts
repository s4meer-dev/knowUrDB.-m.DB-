export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  question: string;
  generated_sql?: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  status: 'success' | 'error';
  error?: string;
}
