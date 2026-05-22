import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Keywords mapping to likely tables
TABLE_KEYWORD_MAP = {
    "invoice": ["invoices", "invoice_items"],
    "invoices": ["invoices", "invoice_items"],
    "payment": ["payments", "receipts"],
    "paid": ["invoices", "payments"],
    "cancelled": ["invoices", "appointments"],
    "cancel": ["invoices", "appointments"],
    "overdue": ["invoices"],
    "patient": ["patients"],
    "patients": ["patients"],
    "appointment": ["appointments"],
    "appointments": ["appointments"],
    "department": ["departments"],
    "departments": ["departments"],
    "doctor": ["employees", "consultations"],
    "employee": ["employees"],
    "employees": ["employees"],
    "consultation": ["consultations"],
    "diagnosis": ["consultations"],
    "receipt": ["receipts"],
    "service": ["services"],
    "revenue": ["invoices", "payments"],
    "ticket": ["tickets"],
    "query": ["query_history"],
    "history": ["query_history"],
    "user": ["users"],
}


class SchemaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._schema_cache: dict[str, Any] | None = None

    async def get_all_tables(self) -> list[str]:
        result = await self.db.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """),
            {"schema": settings.db_schema},
        )
        return [row[0] for row in result.fetchall()]

    async def get_table_schema(self, table_name: str) -> dict[str, Any]:
        col_result = await self.db.execute(
            text("""
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length
                FROM information_schema.columns c
                WHERE c.table_schema = :schema
                  AND c.table_name = :table
                ORDER BY c.ordinal_position
            """),
            {"schema": settings.db_schema, "table": table_name},
        )
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3],
            }
            for row in col_result.fetchall()
        ]

        # Get foreign keys
        fk_result = await self.db.execute(
            text("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = :schema
                  AND tc.table_name = :table
            """),
            {"schema": settings.db_schema, "table": table_name},
        )
        foreign_keys = [
            {
                "column": row[0],
                "references_table": row[1],
                "references_column": row[2],
            }
            for row in fk_result.fetchall()
        ]

        return {"table": table_name, "columns": columns, "foreign_keys": foreign_keys}

    async def get_full_schema(self) -> dict[str, Any]:
        if self._schema_cache:
            return self._schema_cache

        tables = await self.get_all_tables()
        schema: dict[str, Any] = {}
        for table in tables:
            schema[table] = await self.get_table_schema(table)

        self._schema_cache = schema
        return schema

    def get_relevant_tables(self, question: str, all_tables: list[str]) -> list[str]:
        """Identify tables likely relevant to the user's question using keyword matching."""
        question_lower = question.lower()
        words = re.findall(r"\b\w+\b", question_lower)

        relevant: set[str] = set()

        for word in words:
            if word in TABLE_KEYWORD_MAP:
                for table in TABLE_KEYWORD_MAP[word]:
                    if table in all_tables:
                        relevant.add(table)

        # Always include key context tables
        for table in ["invoices", "patients", "appointments"]:
            if table in all_tables and not relevant:
                relevant.add(table)

        # If nothing matched, return most common tables
        if not relevant:
            default = ["invoices", "patients", "appointments", "employees", "departments"]
            relevant = {t for t in default if t in all_tables}

        return sorted(relevant)

    def format_schema_for_prompt(self, schema: dict[str, Any], relevant_tables: list[str]) -> str:
        """Format schema into a concise prompt-friendly string."""
        lines = [
            f"Database Schema (schema name: {settings.db_schema})",
            f"All queries MUST use the schema prefix: {settings.db_schema}.<table_name>",
            "",
        ]

        for table_name in relevant_tables:
            if table_name not in schema:
                continue
            table_info = schema[table_name]
            lines.append(f"TABLE: {settings.db_schema}.{table_name}")

            for col in table_info["columns"]:
                nullable = "" if col["nullable"] else " NOT NULL"
                lines.append(f"  - {col['name']}: {col['type']}{nullable}")

            if table_info["foreign_keys"]:
                lines.append("  Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    lines.append(
                        f"    {fk['column']} -> {settings.db_schema}.{fk['references_table']}.{fk['references_column']}"
                    )
            lines.append("")

        return "\n".join(lines)
