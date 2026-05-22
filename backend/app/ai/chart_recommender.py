from typing import Any
from app.schemas.query import ChartConfig
from app.core.logging import get_logger

logger = get_logger(__name__)

# Keywords suggesting time axis
TIME_KEYWORDS = {"date", "day", "week", "month", "year", "period", "time", "created_at", "updated_at"}
CATEGORY_KEYWORDS = {"status", "type", "category", "department", "method", "gender", "name"}
COUNT_KEYWORDS = {"count", "total", "sum", "amount", "revenue", "quantity", "number"}


def infer_charts(columns: list[dict[str, str]], rows: list[dict[str, Any]]) -> list[ChartConfig]:
    """Infer chart configurations from query result columns and data."""
    if not rows or not columns:
        return []

    charts: list[ChartConfig] = []
    col_names = [c["name"].lower() for c in columns]

    time_cols = [c for c in col_names if any(t in c for t in TIME_KEYWORDS)]
    category_cols = [c for c in col_names if any(t in c for t in CATEGORY_KEYWORDS)]
    numeric_cols = [
        c for c, info in zip(col_names, columns)
        if info["type"] in ("bigint", "integer", "numeric", "double precision", "float", "int8", "int4", "float8")
        or any(k in c for k in COUNT_KEYWORDS)
    ]

    # ── Time series + numeric → Line chart ──
    if time_cols and numeric_cols:
        x_key = time_cols[0]
        y_keys = numeric_cols[:3]
        chart_data = _prepare_data(rows, x_key, y_keys)
        if chart_data:
            charts.append(ChartConfig(
                chart_type="line",
                title=f"Trend: {', '.join(y_keys)} over {x_key}",
                x_key=x_key,
                y_keys=y_keys,
                data=chart_data,
            ))

    # ── Category + numeric → Bar chart ──
    if category_cols and numeric_cols and len(rows) > 1:
        x_key = category_cols[0]
        y_keys = numeric_cols[:2]
        chart_data = _prepare_data(rows, x_key, y_keys)
        if chart_data and len(chart_data) <= 20:
            charts.append(ChartConfig(
                chart_type="bar",
                title=f"{y_keys[0]} by {x_key}",
                x_key=x_key,
                y_keys=y_keys,
                data=chart_data,
            ))

    # ── Category with single numeric → Pie chart (if ≤ 8 distinct values) ──
    if category_cols and numeric_cols and len(rows) <= 8:
        x_key = category_cols[0]
        y_key = numeric_cols[0]
        chart_data = _prepare_data(rows, x_key, [y_key])
        if chart_data and len({d[x_key] for d in chart_data}) <= 8:
            charts.append(ChartConfig(
                chart_type="pie",
                title=f"Distribution: {y_key} by {x_key}",
                x_key=x_key,
                y_keys=[y_key],
                data=chart_data,
            ))

    # ── Fallback: if only numeric columns → KPI summary (return empty charts) ──
    return charts[:3]  # max 3 charts


def _prepare_data(
    rows: list[dict[str, Any]],
    x_key: str,
    y_keys: list[str],
) -> list[dict[str, Any]]:
    """Prepare chart data with proper key casing."""
    # Find actual column keys (case-insensitive matching)
    actual_x = _find_key(rows[0] if rows else {}, x_key)
    actual_ys = [_find_key(rows[0] if rows else {}, y) for y in y_keys]
    actual_ys = [y for y in actual_ys if y]

    if not actual_x or not actual_ys:
        return []

    result = []
    for row in rows:
        entry: dict[str, Any] = {x_key: str(row.get(actual_x, ""))}
        for y_key, actual_y in zip(y_keys, actual_ys):
            val = row.get(actual_y)
            try:
                entry[y_key] = float(val) if val is not None else 0.0
            except (TypeError, ValueError):
                entry[y_key] = 0.0
        result.append(entry)

    return result


def _find_key(row: dict, key: str) -> str | None:
    """Find a key in a dict case-insensitively."""
    for k in row.keys():
        if k.lower() == key.lower():
            return k
    return None
