// TypeScript types matching backend Pydantic models

export interface ColumnSchema {
  name: string;
  type: string;
}

export interface TableSchema {
  name: string;
  columns: ColumnSchema[];
}

export interface SchemaUploadResponse {
  session_id: string;
  tables: TableSchema[];
  table_count: number;
  message: string;
}

export interface QueryRequest {
  session_id: string;
  question: string;
}

export interface QueryResponse {
  session_id: string;
  generated_sql: string;
  result: any;
  error: string | null;
}

export interface ApiError {
  detail: string;
}

export interface AppState {
  sessionId: string | null;
  tables: TableSchema[];
  isLoading: boolean;
  currentQuestion: string;
  queryResult: QueryResponse | null;
  error: string | null;
}
