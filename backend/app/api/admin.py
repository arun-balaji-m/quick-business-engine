from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import require_admin
from app.models.models import User
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)


@router.get("/schema-tables")
async def get_schema_tables(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all tables in the qbe_demo schema (admin only)."""
    result = await db.execute(
        text("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_schema = t.table_schema AND table_name = t.table_name) AS column_count
            FROM information_schema.tables t
            WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """),
        {"schema": settings.db_schema},
    )
    tables = [{"table": row[0], "columns": row[1]} for row in result.fetchall()]
    return {"schema": settings.db_schema, "tables": tables}


@router.get("/row-counts")
async def get_row_counts(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get row counts for all tables (admin only)."""
    tables = [
        "users", "patients", "employees", "departments", "services",
        "appointments", "consultations", "invoices", "invoice_items",
        "payments", "receipts", "tickets", "query_history", "audit_logs",
    ]
    counts = {}
    for table in tables:
        try:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {settings.db_schema}.{table}"))
            counts[table] = result.scalar() or 0
        except Exception:
            counts[table] = "error"

    return {"counts": counts}


@router.post("/reseed")
async def trigger_reseed(
    current_user: Annotated[User, Depends(require_admin)],
    background_tasks: BackgroundTasks,
):
    """Trigger database reseeding (admin only). Runs in background."""
    background_tasks.add_task(_run_reseed)
    return {"message": "Reseeding started in background. Check logs for progress."}


async def _run_reseed():
    """Background task to reseed the database."""
    import subprocess
    import sys
    try:
        subprocess.run(
            [sys.executable, "-m", "app.db.seed.seed_main", "--clear"],
            check=True,
            capture_output=True,
        )
        logger.info("Database reseeding completed successfully")
    except Exception as e:
        logger.error(f"Reseeding failed: {e}")
