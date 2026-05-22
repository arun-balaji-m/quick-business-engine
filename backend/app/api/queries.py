import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chart_recommender import infer_charts
from app.ai.sql_generator import SQLGenerator
from app.ai.sql_validator import validate_sql
from app.core.exceptions import UnsafeSQLException
from app.db.database import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
    QueryHistoryItem,
)
from app.services.export_service import ExportService
from app.services.query_service import QueryService
from app.services.schema_service import SchemaService
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/queries", tags=["Query Engine"])


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Submit a natural language question.

    Flow:
    1. Retrieve relevant schema metadata
    2. Generate SQL via OpenAI
    3. Validate SQL (read-only check)
    4. Execute query
    5. Generate explanation
    6. Infer charts
    7. Save to history + create ticket
    """
    schema_svc = SchemaService(db)
    query_svc = QueryService(db)
    ticket_svc = TicketService(db)
    generator = SQLGenerator()

    # Step 1: Schema retrieval
    all_tables = await schema_svc.get_all_tables()
    relevant_tables = schema_svc.get_relevant_tables(request.question, all_tables)
    full_schema = await schema_svc.get_full_schema()
    schema_context = schema_svc.format_schema_for_prompt(full_schema, relevant_tables)

    # Step 2: Generate SQL
    sql = await generator.generate_sql(request.question, schema_context)

    # Step 3: Validate SQL
    validation = validate_sql(sql)
    if not validation.is_valid:
        raise UnsafeSQLException(validation.error_message or "Invalid SQL generated")

    # Step 4: Execute
    exec_result = await query_svc.execute_query(validation.cleaned_sql, current_user.id)

    # Step 5: Explanation
    explanation = await generator.generate_explanation(
        question=request.question,
        sql=validation.cleaned_sql,
        row_count=exec_result["row_count"],
        columns=[c.name for c in exec_result["columns"]],
        sample_rows=exec_result["rows"][:3],
    )

    # Step 6: Chart inference
    col_dicts = [{"name": c.name, "type": c.type} for c in exec_result["columns"]]
    charts = infer_charts(col_dicts, exec_result["rows"])

    # Step 7: Save history
    history = await query_svc.save_query_history(
        user_id=current_user.id,
        question=request.question,
        generated_sql=validation.cleaned_sql,
        explanation=explanation,
        result_count=exec_result["row_count"],
        execution_time_ms=exec_result["execution_time_ms"],
        is_successful=True,
        tables_used=relevant_tables,
    )

    # Create ticket
    ticket = await ticket_svc.create_ticket(
        user_id=current_user.id,
        title=request.question[:255],
        query_id=history.id,
    )

    return QueryResponse(
        id=history.id,
        question=request.question,
        generated_sql=validation.cleaned_sql,
        explanation=explanation,
        columns=exec_result["columns"],
        rows=exec_result["rows"],
        row_count=exec_result["row_count"],
        execution_time_ms=exec_result["execution_time_ms"],
        ticket_id=ticket.id,
        charts=charts,
    )


@router.get("/history", response_model=QueryHistoryResponse)
async def get_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Get paginated query history for the current user."""
    query_svc = QueryService(db)
    items, total = await query_svc.get_history(current_user.id, page, page_size)

    return QueryHistoryResponse(
        items=[QueryHistoryItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{query_id}/export/csv")
async def export_csv(
    query_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Re-execute a previous query and export results as CSV."""
    from sqlalchemy import select
    from app.models.models import QueryHistory
    from app.core.exceptions import NotFoundException, ForbiddenException

    result = await db.execute(select(QueryHistory).where(QueryHistory.id == query_id))
    query = result.scalar_one_or_none()
    if not query:
        raise NotFoundException("Query")
    if query.user_id != current_user.id:
        raise ForbiddenException()

    query_svc = QueryService(db)
    exec_result = await query_svc.execute_query(query.generated_sql, current_user.id)

    export_svc = ExportService()
    col_names = [c.name for c in exec_result["columns"]]
    csv_bytes = export_svc.export_csv(col_names, exec_result["rows"])

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="qube_query_{query_id}.csv"'},
    )


@router.get("/{query_id}/export/excel")
async def export_excel(
    query_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Re-execute a previous query and export results as Excel."""
    from sqlalchemy import select
    from app.models.models import QueryHistory
    from app.core.exceptions import NotFoundException, ForbiddenException

    result = await db.execute(select(QueryHistory).where(QueryHistory.id == query_id))
    query = result.scalar_one_or_none()
    if not query:
        raise NotFoundException("Query")
    if query.user_id != current_user.id:
        raise ForbiddenException()

    query_svc = QueryService(db)
    exec_result = await query_svc.execute_query(query.generated_sql, current_user.id)

    export_svc = ExportService()
    col_names = [c.name for c in exec_result["columns"]]
    excel_bytes = export_svc.export_excel(col_names, exec_result["rows"])

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="qube_query_{query_id}.xlsx"'},
    )
