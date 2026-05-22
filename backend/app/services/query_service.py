import time
from typing import Any

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnsafeSQLException, DatabaseException
from app.core.logging import get_logger
from app.models.models import QueryHistory, User
from app.schemas.query import QueryResultColumn

logger = get_logger(__name__)


class QueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_query(
        self, sql: str, user_id: int
    ) -> dict[str, Any]:
        """Execute a validated SQL query and return structured results."""
        start = time.monotonic()
        try:
            # Set statement timeout for safety
            await self.db.execute(
                text(f"SET LOCAL statement_timeout = '{settings.query_timeout_seconds * 1000}'")
            )

            result = await self.db.execute(text(sql))
            rows_raw = result.fetchmany(settings.max_result_rows)
            col_names = list(result.keys()) if result.keys() else []

            elapsed_ms = int((time.monotonic() - start) * 1000)

            rows = [dict(zip(col_names, row)) for row in rows_raw]

            # Serialize non-JSON-safe types
            rows = [self._serialize_row(r) for r in rows]

            columns = [
                QueryResultColumn(
                    name=col,
                    type=self._infer_python_type(rows[0].get(col) if rows else None),
                )
                for col in col_names
            ]

            logger.info(
                f"Query executed: {len(rows)} rows in {elapsed_ms}ms for user {user_id}"
            )

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(f"Query execution error: {e}")
            raise DatabaseException(f"Query execution failed: {str(e)}")

    async def save_query_history(
        self,
        user_id: int,
        question: str,
        generated_sql: str,
        explanation: str,
        result_count: int,
        execution_time_ms: int,
        is_successful: bool,
        tables_used: list[str],
        error_message: str | None = None,
    ) -> QueryHistory:
        import json

        history = QueryHistory(
            user_id=user_id,
            question=question,
            generated_sql=generated_sql,
            explanation=explanation,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            is_successful=is_successful,
            error_message=error_message,
            tables_used=json.dumps(tables_used),
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return history

    async def get_history(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[QueryHistory], int]:
        offset = (page - 1) * page_size

        total_result = await self.db.execute(
            select(func.count()).select_from(QueryHistory).where(QueryHistory.user_id == user_id)
        )
        total = total_result.scalar() or 0

        result = await self.db.execute(
            select(QueryHistory)
            .where(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total

    def _serialize_row(self, row: dict) -> dict:
        """Convert non-JSON-serializable types to strings."""
        from decimal import Decimal
        from datetime import date, datetime

        serialized = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                serialized[k] = float(v)
            elif isinstance(v, (datetime, date)):
                serialized[k] = v.isoformat()
            elif v is None:
                serialized[k] = None
            else:
                serialized[k] = v
        return serialized

    def _infer_python_type(self, value: Any) -> str:
        if isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, str):
            return "string"
        else:
            return "string"
