// API Types matching FastAPI backend schemas

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: "admin" | "analyst" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Query types
export interface QueryResultColumn {
  name: string;
  type: string;
}

export interface ChartConfig {
  chart_type: "bar" | "line" | "pie" | "area";
  title: string;
  x_key: string;
  y_keys: string[];
  data: Record<string, unknown>[];
}

export interface QueryResponse {
  id: number;
  question: string;
  generated_sql: string;
  explanation: string;
  columns: QueryResultColumn[];
  rows: Record<string, unknown>[];
  row_count: number;
  execution_time_ms: number;
  ticket_id: number | null;
  charts: ChartConfig[];
}

export interface QueryHistoryItem {
  id: number;
  question: string;
  generated_sql: string | null;
  explanation: string | null;
  result_count: number | null;
  execution_time_ms: number | null;
  is_successful: boolean;
  tables_used: string | null;
  created_at: string;
}

export interface QueryHistoryResponse {
  items: QueryHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Ticket types
export type TicketStatus = "OPEN" | "IN_PROGRESS" | "CLOSED";

export interface TicketQuerySummary {
  id: number;
  question: string;
  generated_sql: string | null;
  execution_time_ms: number | null;
  result_count: number | null;
  created_at: string;
}

export interface Ticket {
  id: number;
  ticket_number: string;
  user_id: number;
  query_id: number | null;
  status: TicketStatus;
  title: string;
  description: string | null;
  resolution_notes: string | null;
  is_satisfied: boolean | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
  query: TicketQuerySummary | null;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TicketCloseRequest {
  is_satisfied: boolean;
  resolution_notes?: string;
}

// Dashboard types
export interface KPICard {
  label: string;
  value: string;
  subtitle?: string;
  trend?: number;
}

export interface DashboardMetrics {
  total_queries: number;
  open_tickets: number;
  closed_tickets: number;
  avg_execution_time_ms: number;
  success_rate: number;
  queries_today: number;
  kpi_cards: KPICard[];
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface DashboardChartData {
  invoice_status_distribution: ChartDataPoint[];
  appointment_by_department: ChartDataPoint[];
  appointments_trend: Record<string, unknown>[];
  invoice_revenue_trend: Record<string, unknown>[];
  queries_trend: Record<string, unknown>[];
}

// API error
export interface APIError {
  detail: string;
  error_type?: string;
}
