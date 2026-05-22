import re
from app.core.exceptions import AIServiceException
from app.core.logging import get_logger
from app.ai.openai_client import get_openai_client
from app.core.config import settings

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert PostgreSQL query generator for a healthcare business analytics platform.

Your task is to generate SAFE, READ-ONLY PostgreSQL SELECT queries based on the user's natural language question.

CRITICAL RULES:
1. Generate ONLY SELECT statements. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any other DML/DDL.
2. Always use the schema prefix provided in the schema description.
3. Use proper table aliases for clarity.
4. Add meaningful ORDER BY clauses when relevant.
5. Limit results to {max_rows} rows unless the user specifies a different limit.
6. Use ILIKE for case-insensitive text searches.
7. Use date functions like NOW(), CURRENT_DATE, date_trunc() for time-based queries.
8. "Yesterday" means: WHERE date_column >= CURRENT_DATE - INTERVAL '1 day' AND date_column < CURRENT_DATE
9. "Last week" means: WHERE date_column >= CURRENT_DATE - INTERVAL '7 days'
10. "Last month" means: WHERE date_column >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
11. Return ONLY the SQL query — no explanations, no markdown fences, no commentary.
12. If the question is ambiguous, generate the most reasonable interpretation.

STATUS VALUES TO KNOW:
- Invoice statuses: 'draft', 'sent', 'paid', 'cancelled', 'overdue'
- Appointment statuses: 'scheduled', 'completed', 'cancelled', 'no_show'
- Ticket statuses: 'OPEN', 'IN_PROGRESS', 'CLOSED'
"""

EXPLANATION_PROMPT = """You are a business analyst helping users understand data query results.

Given the SQL query and user question, provide a brief, clear explanation:
1. What data was retrieved (1-2 sentences)
2. Key insights from the results (2-3 bullet points if data is present)
3. If no results: suggest why and what to try next

Keep the explanation concise, professional, and business-focused.
Do NOT repeat the SQL query in your explanation."""


class SQLGenerator:
    async def generate_sql(self, question: str, schema_context: str) -> str:
        client = get_openai_client()

        system_prompt = SYSTEM_PROMPT.format(max_rows=settings.max_result_rows)

        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\n\n{schema_context}"},
                    {"role": "user", "content": question},
                ],
                temperature=settings.openai_temperature,
                max_tokens=1000,
            )

            sql = response.choices[0].message.content or ""
            sql = self._clean_sql(sql)
            logger.info(f"Generated SQL for question: {question[:50]}...")
            return sql

        except Exception as e:
            logger.error(f"OpenAI SQL generation failed: {e}")
            raise AIServiceException(f"Failed to generate SQL: {str(e)}")

    async def generate_explanation(
        self,
        question: str,
        sql: str,
        row_count: int,
        columns: list[str],
        sample_rows: list[dict],
    ) -> str:
        client = get_openai_client()

        data_summary = f"Query returned {row_count} rows."
        if columns:
            data_summary += f" Columns: {', '.join(columns)}."
        if sample_rows and row_count > 0:
            data_summary += f" First row sample: {sample_rows[0]}"

        user_message = f"""User question: {question}

SQL executed:
{sql}

Results summary:
{data_summary}

Provide a business-friendly explanation of these results."""

        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": EXPLANATION_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            return response.choices[0].message.content or "Query executed successfully."
        except Exception as e:
            logger.warning(f"Explanation generation failed: {e}")
            return f"Query returned {row_count} row(s) successfully."

    def _clean_sql(self, sql: str) -> str:
        """Strip markdown fences and whitespace from LLM output."""
        sql = sql.strip()
        # Remove ```sql ... ``` or ``` ... ```
        sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\s*```$", "", sql)
        sql = sql.strip()
        # Ensure it ends with semicolon removed (we add it back clean)
        sql = sql.rstrip(";").strip()
        return sql
