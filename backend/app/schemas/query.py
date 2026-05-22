from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)


class QueryResultColumn(BaseModel):
    name: str
    type: str


class ChartConfig(BaseModel):
    chart_type: str  # bar, line, pie, area
    title: str
    x_key: str
    y_keys: list[str]
    data: list[dict[str, Any]]


class QueryResponse(BaseModel):
    id: int
    question: str
    generated_sql: str
    explanation: str
    columns: list[QueryResultColumn]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: int
    ticket_id: int | None = None
    charts: list[ChartConfig] = []

    model_config = {"from_attributes": True}


class QueryHistoryItem(BaseModel):
    id: int
    question: str
    generated_sql: str | None
    explanation: str | None
    result_count: int | None
    execution_time_ms: int | None
    is_successful: bool
    tables_used: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryHistoryResponse(BaseModel):
    items: list[QueryHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class SQLValidationResult(BaseModel):
    is_valid: bool
    cleaned_sql: str
    error_message: str | None = None
