export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface AiStatusResponse {
  configured: boolean;
  status: string;
  provider: string;
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
  query_source?: string;
  explanation?: string;
  follow_up_suggestions?: string[];
}

export interface HistoryItem {
  id: string;
  question: string;
  generated_sql?: string;
  status: 'success' | 'error';
  row_count: number;
  execution_time_ms: number;
  error?: string;
  query_source?: string;
  created_at: string;
}

export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
}

export interface Suggestion {
  question: string;
  category: string;
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
}

export interface ColumnInfo {
  name: string;
  type: string;
  primary_key: boolean;
  foreign_key?: {
    table: string;
    column: string;
  } | null;
}

export interface TableInfo {
  table_name: string;
  columns: ColumnInfo[];
  row_count: number;
}

export interface SchemaSummary {
  tables: string[];
  total_tables: number;
}
