import re
from app.schemas.query import SQLValidationResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Operations that are NEVER allowed
BLOCKED_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bMERGE\b",
    r"\bEXECUTE\b",
    r"\bEXEC\b",
    r"\bCALL\b",
    r"\bCOPY\b",
    r"\bPG_READ_FILE\b",
    r"\bPG_WRITE_FILE\b",
    r"--",           # SQL comment (potential injection)
    r";\s*\w",       # Stacked queries
]

# SQL injection probes
INJECTION_PATTERNS = [
    r"'.*OR.*'.*=.*'",
    r"UNION\s+ALL\s+SELECT",
    r"UNION\s+SELECT",
]


def validate_sql(sql: str) -> SQLValidationResult:
    if not sql or not sql.strip():
        return SQLValidationResult(
            is_valid=False,
            cleaned_sql="",
            error_message="Empty SQL query",
        )

    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return SQLValidationResult(
            is_valid=False,
            cleaned_sql=sql,
            error_message="Only SELECT queries are allowed. Got: " + sql_upper.split()[0] if sql_upper.split() else "empty",
        )

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            matched = re.search(pattern, sql_upper, re.IGNORECASE)
            logger.warning(f"Blocked SQL pattern detected: {pattern} in query: {sql[:100]}")
            return SQLValidationResult(
                is_valid=False,
                cleaned_sql=sql,
                error_message=f"Query contains forbidden operation: {matched.group() if matched else pattern}",
            )

    # Check injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            logger.warning(f"SQL injection pattern detected: {pattern}")
            return SQLValidationResult(
                is_valid=False,
                cleaned_sql=sql,
                error_message="Query contains potentially unsafe patterns",
            )

    return SQLValidationResult(is_valid=True, cleaned_sql=sql)
