import api from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  Token,
  User,
  QueryResponse,
  QueryHistoryResponse,
  TicketListResponse,
  Ticket,
  TicketCloseRequest,
  DashboardMetrics,
  DashboardChartData,
} from "@/types/api";

// ─── Auth ──────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: LoginRequest) =>
    api.post<Token>("/auth/login", data).then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/change-password", data).then((r) => r.data),
};

// ─── Queries ───────────────────────────────────────────────────────────────

export const queryApi = {
  ask: (question: string) =>
    api.post<QueryResponse>("/queries/ask", { question }).then((r) => r.data),

  history: (page = 1, page_size = 20) =>
    api
      .get<QueryHistoryResponse>("/queries/history", { params: { page, page_size } })
      .then((r) => r.data),

  exportCsv: (queryId: number) =>
    api
      .get(`/queries/${queryId}/export/csv`, { responseType: "blob" })
      .then((r) => r.data),

  exportExcel: (queryId: number) =>
    api
      .get(`/queries/${queryId}/export/excel`, { responseType: "blob" })
      .then((r) => r.data),
};

// ─── Tickets ───────────────────────────────────────────────────────────────

export const ticketApi = {
  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    api.get<TicketListResponse>("/tickets", { params }).then((r) => r.data),

  get: (id: number) => api.get<Ticket>(`/tickets/${id}`).then((r) => r.data),

  close: (id: number, data: TicketCloseRequest) =>
    api.post<Ticket>(`/tickets/${id}/close`, data).then((r) => r.data),

  update: (id: number, data: { status?: string; resolution_notes?: string }) =>
    api.patch<Ticket>(`/tickets/${id}`, data).then((r) => r.data),
};

// ─── Dashboard ─────────────────────────────────────────────────────────────

export const dashboardApi = {
  metrics: () =>
    api.get<DashboardMetrics>("/dashboard/metrics").then((r) => r.data),

  charts: () =>
    api.get<DashboardChartData>("/dashboard/charts").then((r) => r.data),
};

// ─── Admin ─────────────────────────────────────────────────────────────────

export const adminApi = {
  schemaTables: () =>
    api.get("/admin/schema-tables").then((r) => r.data),

  rowCounts: () =>
    api.get("/admin/row-counts").then((r) => r.data),

  reseed: () =>
    api.post("/admin/reseed").then((r) => r.data),
};
