"""
QuBE Database Seeder

Usage:
    python -m app.db.seed.seed_main              # Seed all tables
    python -m app.db.seed.seed_main --clear      # Clear and reseed
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Allow running as script from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text
from app.db.database import AsyncSessionLocal, engine
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger("seeder")


async def create_schema(session):
    logger.info(f"Creating schema '{settings.db_schema}' if not exists...")
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
    await session.commit()


async def truncate_all(session):
    logger.info("Clearing existing data...")
    tables = [
        "dashboard_cache", "audit_logs", "query_history", "tickets",
        "receipts", "payments", "invoice_items", "invoices",
        "consultations", "appointments", "services", "patients",
        "employees", "departments", "users",
    ]
    for table in tables:
        try:
            await session.execute(
                text(f"TRUNCATE TABLE {settings.db_schema}.{table} RESTART IDENTITY CASCADE")
            )
        except Exception as e:
            logger.warning(f"Could not truncate {table}: {e}")
    await session.commit()
    logger.info("All tables cleared.")


async def run_seed(clear: bool = False):
    from app.models.models import Base

    # Import all seeders
    from app.db.seed.seeders import (
        seed_departments,
        seed_employees,
        seed_patients,
        seed_services,
        seed_appointments,
        seed_consultations,
        seed_invoices,
        seed_payments_and_receipts,
        seed_users,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await create_schema(session)

        if clear:
            await truncate_all(session)

        logger.info("Starting data seeding...")

        await seed_users(session)
        await seed_departments(session)
        await seed_employees(session)
        await seed_patients(session)
        await seed_services(session)
        await seed_appointments(session)
        await seed_consultations(session)
        await seed_invoices(session)
        await seed_payments_and_receipts(session)

        await session.commit()
        logger.info("✅ All data seeded successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QuBE Database Seeder")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()

    asyncio.run(run_seed(clear=args.clear))
