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

export interface QuerySourceCitation {
  source_id: string;
  name: string;
  type: string;
  table?: string;
  page?: number;
}

export interface ClarificationCandidate {
  source_id: string;
  name: string;
}

export interface QueryRequest {
  question: string;
  source_ids?: string[];
}

export interface QueryResponse {
  question: string;
  generated_sql?: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  status: 'success' | 'clarification_required' | 'error';
  error?: string;
  query_source?: string;
  explanation?: string;
  follow_up_suggestions?: string[];
  sources?: QuerySourceCitation[];
  candidates?: ClarificationCandidate[];
  confidence?: number;
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

export interface SourceMetadata {
  source_id: string;
  name: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  detected_format: string;
  detected_dialect?: string;
  size_bytes: number;
  uploaded_at: string;
  status: 'uploading' | 'analyzing' | 'indexing' | 'ready' | 'failed' | 'deleting' | 'deleted';
  table_count?: number;
  record_count?: number;
  schema_summary?: any;
  error_message?: string;
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
