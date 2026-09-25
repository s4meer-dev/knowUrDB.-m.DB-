export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  database?: {
    connected: boolean;
    engine: string;
    version?: string;
    database?: string;
  };
}

export interface Answer {
  headline?: string;
  value?: string;
  unit?: string;
  summary?: string;
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
  collection?: string;
  page?: number;
}

export interface ClarificationCandidate {
  source_id: string;
  name: string;
  collection?: string;
  document_count?: number;
  field_count?: number;
  fields_preview?: string[];
  description?: string;
}

export interface PresentationContract {
  type:
    | 'table'
    | 'kpi'
    | 'ranked_table'
    | 'comparison'
    | 'chart'
    | 'detail'
    | 'dataset_overview'
    | 'collection_overview'
    | 'schema'
    | 'document_answer'
    | 'clarification'
    | 'empty'
    | 'error';
  title?: string;
  subtitle?: string;
  summary?: string;
  primary_value?: string;
  primary_unit?: string;
  chart_type?: string;
  highlight_record?: Record<string, any>;
  candidate_collections?: ClarificationCandidate[];
  multi_collection_sources?: string[];
  collections_summary?: Array<{
    collection: string;
    documents: number;
    fields: number;
    key_fields: string;
  }>;
  schema_fields?: Array<{
    collection: string;
    field: string;
    type: string;
    sample_values: string;
  }>;
  show_technical_by_default?: boolean;
}

export interface QueryRequest {
  question: string;
  source_ids?: string[];
  active_collection?: string;
  conversation_context?: Record<string, any>;
}

export interface QueryResponse {
  question: string;
  intent?: string;
  collection?: string;
  query_plan?: Record<string, any>;
  presentation?: PresentationContract;
  generated_mongo_query?: string;
  structured_query?: Record<string, any>;
  generated_sql?: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  status: 'success' | 'clarification_required' | 'error';
  error?: string;
  error_code?: string;
  query_source?: string;
  answer?: Answer;
  insights?: string[];
  follow_up_suggestions?: string[];
  sources?: QuerySourceCitation[];
  candidates?: ClarificationCandidate[];
  confidence?: number;
}

export interface HistoryItem {
  id: string;
  question: string;
  generated_mongo_query?: string;
  generated_sql?: string;
  status: 'success' | 'error';
  row_count: number;
  execution_time_ms: number;
  error?: string;
  error_message?: string;
  query_source?: string;
  source_id?: string;
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
  data_type?: string;
  primary_key: boolean;
  nullable?: boolean;
  is_nested?: boolean;
  is_array?: boolean;
  sample_values?: any[];
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

export interface IndexInfo {
  name: string;
  keys: string[];
  unique: boolean;
}

export interface TableInfo {
  name: string;
  document_count?: number;
  columns: ColumnInfo[];
  primary_keys: string[];
  foreign_keys: ForeignKeyInfo[];
  indexes?: IndexInfo[];
  sample_document?: Record<string, any> | null;
}

export interface DatabaseSchema {
  tables: TableInfo[];
  collections?: TableInfo[];
}

export interface SchemaSummary {
  summary: string;
}

export interface SourceMetadata {
  source_id: string;
  name: string;
  display_name?: string;
  domain?: string;
  description?: string;
  source_category?: 'mongodb' | 'uploaded_file' | string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  detected_format: string;
  detected_dialect?: string;
  size_bytes: number;
  uploaded_at: string;
  status: 'uploading' | 'analyzing' | 'indexing' | 'ready' | 'failed' | 'deleting' | 'deleted';
  database_name?: string;
  collections?: string[];
  collection_counts?: Record<string, number>;
  table_count?: number;
  record_count?: number;
  index_count?: number;
  schema_summary?: any;
  manifest?: Record<string, any>;
  filesystem_path?: string;
  sync_status?: string;
  dataset_artifacts?: string[];
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
