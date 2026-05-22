from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.dashboard import DashboardMetrics, DashboardChartData, KPICard, ChartDataPoint

logger = get_logger(__name__)
S = settings.db_schema


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_metrics(self, user_id: int) -> DashboardMetrics:
        # Query stats
        stats = await self.db.execute(
            text(f"""
                SELECT
                    COUNT(*) AS total_queries,
                    COUNT(*) FILTER (WHERE is_successful) AS successful,
                    AVG(execution_time_ms) AS avg_exec_ms,
                    COUNT(*) FILTER (WHERE DATE(created_at) = CURRENT_DATE) AS today_count
                FROM {S}.query_history
                WHERE user_id = :uid
            """),
            {"uid": user_id},
        )
        q_row = stats.fetchone()
        total_q = q_row[0] or 0
        successful = q_row[1] or 0
        avg_ms = float(q_row[2] or 0)
        today_count = q_row[3] or 0

        # Ticket stats
        ticket_stats = await self.db.execute(
            text(f"""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'OPEN') AS open_count,
                    COUNT(*) FILTER (WHERE status = 'CLOSED') AS closed_count
                FROM {S}.tickets
                WHERE user_id = :uid
            """),
            {"uid": user_id},
        )
        t_row = ticket_stats.fetchone()
        open_tickets = t_row[0] or 0
        closed_tickets = t_row[1] or 0

        success_rate = (successful / total_q * 100) if total_q > 0 else 0.0

        kpi_cards = [
            KPICard(label="Total Queries", value=str(total_q), subtitle="All time"),
            KPICard(label="Open Tickets", value=str(open_tickets), subtitle="Awaiting review"),
            KPICard(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                subtitle="Query success",
            ),
            KPICard(
                label="Avg Response",
                value=f"{avg_ms:.0f}ms",
                subtitle="Query execution time",
            ),
        ]

        return DashboardMetrics(
            total_queries=total_q,
            open_tickets=open_tickets,
            closed_tickets=closed_tickets,
            avg_execution_time_ms=avg_ms,
            success_rate=success_rate,
            queries_today=today_count,
            kpi_cards=kpi_cards,
        )

    async def get_chart_data(self) -> DashboardChartData:
        # Invoice status distribution
        inv_dist = await self.db.execute(
            text(f"""
                SELECT status, COUNT(*) AS count
                FROM {S}.invoices
                GROUP BY status
                ORDER BY count DESC
            """)
        )
        invoice_status = [
            ChartDataPoint(label=row[0].capitalize(), value=float(row[1]))
            for row in inv_dist.fetchall()
        ]

        # Appointments by department
        appt_dept = await self.db.execute(
            text(f"""
                SELECT d.name, COUNT(a.id) AS count
                FROM {S}.appointments a
                JOIN {S}.departments d ON a.department_id = d.id
                GROUP BY d.name
                ORDER BY count DESC
                LIMIT 10
            """)
        )
        appt_by_dept = [
            ChartDataPoint(label=row[0], value=float(row[1]))
            for row in appt_dept.fetchall()
        ]

        # Appointment trend (last 30 days)
        appt_trend = await self.db.execute(
            text(f"""
                SELECT
                    TO_CHAR(DATE_TRUNC('day', appointment_date), 'MM-DD') AS day,
                    COUNT(*) AS appointments
                FROM {S}.appointments
                WHERE appointment_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', appointment_date)
                ORDER BY DATE_TRUNC('day', appointment_date)
            """)
        )
        appointments_trend = [
            {"day": row[0], "appointments": int(row[1])}
            for row in appt_trend.fetchall()
        ]

        # Invoice revenue trend (last 12 months)
        rev_trend = await self.db.execute(
            text(f"""
                SELECT
                    TO_CHAR(DATE_TRUNC('month', created_at), 'Mon YYYY') AS month,
                    SUM(total_amount) FILTER (WHERE status = 'paid') AS revenue,
                    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled
                FROM {S}.invoices
                WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY DATE_TRUNC('month', created_at)
            """)
        )
        revenue_trend = [
            {
                "month": row[0],
                "revenue": float(row[1] or 0),
                "cancelled": int(row[2] or 0),
            }
            for row in rev_trend.fetchall()
        ]

        # Queries trend (last 14 days)
        q_trend = await self.db.execute(
            text(f"""
                SELECT
                    TO_CHAR(DATE(created_at), 'MM-DD') AS day,
                    COUNT(*) AS queries
                FROM {S}.query_history
                WHERE created_at >= CURRENT_DATE - INTERVAL '14 days'
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """)
        )
        queries_trend = [
            {"day": row[0], "queries": int(row[1])}
            for row in q_trend.fetchall()
        ]

        return DashboardChartData(
            invoice_status_distribution=invoice_status,
            appointment_by_department=appt_by_dept,
            appointments_trend=appointments_trend,
            invoice_revenue_trend=revenue_trend,
            queries_trend=queries_trend,
        )
