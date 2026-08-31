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

export interface ForeignKeyInfo {
  source_column: string;
  referenced_table: string;
  referenced_column: string;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
  primary_keys: string[];
  foreign_keys: ForeignKeyInfo[];
}

export interface DatabaseSchema {
  tables: TableInfo[];
}

export interface SchemaSummary {
  summary: string;
}

export interface DatabaseStatusResponse {
  is_demo: boolean;
  name: string;
  path: string;
  format?: string;
  dialect?: string;
  table_count?: number;
  record_count?: number;
}

export interface BasicResponse {
  status: string;
  message: string;
}
