from datetime import datetime
from pydantic import BaseModel, Field

from app.models.models import TicketStatus


class TicketCreate(BaseModel):
    query_id: int | None = None
    title: str = Field(..., min_length=5, max_length=255)
    description: str | None = None


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    resolution_notes: str | None = None


class TicketCloseRequest(BaseModel):
    is_satisfied: bool
    resolution_notes: str | None = None


class TicketQuerySummary(BaseModel):
    id: int
    question: str
    generated_sql: str | None
    execution_time_ms: int | None
    result_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    user_id: int
    query_id: int | None
    status: TicketStatus
    title: str
    description: str | None
    resolution_notes: str | None
    is_satisfied: bool | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    query: TicketQuerySummary | None = None

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
