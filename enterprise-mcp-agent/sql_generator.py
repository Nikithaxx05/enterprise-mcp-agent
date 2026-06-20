from __future__ import annotations

import os
from typing import Any


SCHEMA_CONTEXT = """
Tables:
- customers(id, name, industry, annual_revenue, risk_score)
- invoices(id, customer_id, amount, status, due_date)
- support_tickets(id, customer_id, issue_type, priority, status)
- workflows(id, department, process_name, manual_steps, avg_time_minutes, frequency_per_month)
"""


def generate_sql(question: str) -> tuple[str, tuple[Any, ...], str]:
    """Generate SQL from natural language with an offline default and optional LLM hook.

    The default mode intentionally avoids external API calls. If a production team wants
    an actual LLM provider, they can wire it into the provider branch and still run the
    returned SQL through server.execute_read_only_sql before execution.
    """
    provider = os.getenv("ENTERPRISE_SQL_LLM_PROVIDER", "offline").lower()
    if provider != "offline":
        return (
            "SELECT name, industry, annual_revenue, risk_score FROM customers ORDER BY risk_score DESC LIMIT 10",
            (),
            f"LLM provider '{provider}' is configured, but no external provider adapter is enabled in this no-API demo. Used the safe offline SQL fallback:",
        )

    normalized = question.lower()
    if "count" in normalized and "record" in normalized:
        return (
            """
            SELECT 'customers' AS table_name, COUNT(*) AS record_count FROM customers
            UNION ALL
            SELECT 'invoices', COUNT(*) FROM invoices
            UNION ALL
            SELECT 'support_tickets', COUNT(*) FROM support_tickets
            UNION ALL
            SELECT 'workflows', COUNT(*) FROM workflows
            """,
            (),
            "Generated read-only SQL for record counts:",
        )
    if "workflow" in normalized and ("top" in normalized or "automation" in normalized):
        return (
            """
            SELECT department, process_name,
                   manual_steps * avg_time_minutes * frequency_per_month / 60.0 AS monthly_hours
            FROM workflows
            ORDER BY monthly_hours DESC
            LIMIT 10
            """,
            (),
            "Generated read-only SQL for top workflow automation candidates:",
        )

    return (
        "SELECT name, industry, annual_revenue, risk_score FROM customers ORDER BY risk_score DESC LIMIT 10",
        (),
        "Generated read-only SQL with the offline natural-language SQL planner:",
    )
