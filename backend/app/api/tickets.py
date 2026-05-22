import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_active_user
from app.models.models import User, TicketStatus
from app.schemas.ticket import (
    TicketCloseRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: TicketStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all tickets for the current user."""
    svc = TicketService(db)
    items, total = await svc.list_tickets(current_user.id, status, page, page_size)

    return TicketListResponse(
        items=[TicketResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific ticket by ID."""
    svc = TicketService(db)
    ticket = await svc.get_ticket(ticket_id, current_user.id)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update ticket status or resolution notes."""
    svc = TicketService(db)
    ticket = await svc.update_ticket(ticket_id, current_user.id, update)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/close", response_model=TicketResponse)
async def close_ticket(
    ticket_id: int,
    close_req: TicketCloseRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Close a ticket with satisfaction feedback."""
    svc = TicketService(db)
    ticket = await svc.close_ticket(ticket_id, current_user.id, close_req)
    return TicketResponse.model_validate(ticket)
