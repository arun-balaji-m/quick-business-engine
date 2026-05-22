import random
import string
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.logging import get_logger
from app.models.models import Ticket, TicketStatus, QueryHistory
from app.schemas.ticket import TicketCloseRequest, TicketUpdate

logger = get_logger(__name__)


def _generate_ticket_number() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TKT-{suffix}"


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(
        self,
        user_id: int,
        title: str,
        query_id: int | None = None,
        description: str | None = None,
    ) -> Ticket:
        ticket = Ticket(
            ticket_number=_generate_ticket_number(),
            user_id=user_id,
            query_id=query_id,
            title=title,
            description=description,
            status=TicketStatus.open,
        )
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        logger.info(f"Ticket created: {ticket.ticket_number} for user {user_id}")
        return ticket

    async def get_ticket(self, ticket_id: int, user_id: int) -> Ticket:
        result = await self.db.execute(
            select(Ticket)
            .options(selectinload(Ticket.query))
            .where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise NotFoundException("Ticket")
        if ticket.user_id != user_id:
            raise ForbiddenException("You do not have access to this ticket")
        return ticket

    async def list_tickets(
        self,
        user_id: int,
        status: TicketStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ticket], int]:
        offset = (page - 1) * page_size

        query = select(Ticket).where(Ticket.user_id == user_id)
        count_query = select(func.count()).select_from(Ticket).where(Ticket.user_id == user_id)

        if status:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query
            .options(selectinload(Ticket.query))
            .order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total

    async def update_ticket(
        self, ticket_id: int, user_id: int, update: TicketUpdate
    ) -> Ticket:
        ticket = await self.get_ticket(ticket_id, user_id)

        if update.status is not None:
            ticket.status = update.status
        if update.resolution_notes is not None:
            ticket.resolution_notes = update.resolution_notes

        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def close_ticket(
        self, ticket_id: int, user_id: int, close_req: TicketCloseRequest
    ) -> Ticket:
        ticket = await self.get_ticket(ticket_id, user_id)

        ticket.status = TicketStatus.closed
        ticket.is_satisfied = close_req.is_satisfied
        ticket.closed_at = datetime.now(timezone.utc)
        if close_req.resolution_notes:
            ticket.resolution_notes = close_req.resolution_notes

        await self.db.flush()
        await self.db.refresh(ticket)
        logger.info(
            f"Ticket {ticket.ticket_number} closed. Satisfied: {close_req.is_satisfied}"
        )
        return ticket

    async def get_open_ticket_count(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.user_id == user_id, Ticket.status == TicketStatus.open)
        )
        return result.scalar() or 0
