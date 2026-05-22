from pydantic import BaseModel
from typing import Any


class KPICard(BaseModel):
    label: str
    value: str
    subtitle: str | None = None
    trend: float | None = None  # percentage change


class DashboardMetrics(BaseModel):
    total_queries: int
    open_tickets: int
    closed_tickets: int
    avg_execution_time_ms: float
    success_rate: float
    queries_today: int
    kpi_cards: list[KPICard]


class ChartDataPoint(BaseModel):
    label: str
    value: float


class DashboardChartData(BaseModel):
    invoice_status_distribution: list[ChartDataPoint]
    appointment_by_department: list[ChartDataPoint]
    appointments_trend: list[dict[str, Any]]
    invoice_revenue_trend: list[dict[str, Any]]
    queries_trend: list[dict[str, Any]]
