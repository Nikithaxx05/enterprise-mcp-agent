from __future__ import annotations

import re
import sqlite3
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

from sql_generator import generate_sql
from synthetic_data import generate_synthetic_records
from vector_search import LocalVectorIndex


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "enterprise.db"
DOCUMENTS_DIR = BASE_DIR / "documents"
SYNTHETIC_CUSTOMER_COUNT = 50_000

FORBIDDEN_SQL = re.compile(r"\b(drop|delete|update|insert|alter|create|replace|truncate|attach|detach|pragma)\b", re.I)

mcp = FastMCP("enterprise-mcp-agent")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seed_database() -> None:
    """Create and seed the local SQLite database if it does not already exist."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                industry TEXT NOT NULL,
                annual_revenue REAL NOT NULL,
                risk_score INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                due_date TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY,
                department TEXT NOT NULL,
                process_name TEXT NOT NULL,
                manual_steps INTEGER NOT NULL,
                avg_time_minutes INTEGER NOT NULL,
                frequency_per_month INTEGER NOT NULL
            );
            """
        )

        existing = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

        if existing == 0:
            today = date.today()
            customers = [
                (1, "Acme Manufacturing", "Manufacturing", 18_500_000, 72),
                (2, "Nimbus Health Group", "Healthcare", 42_000_000, 58),
                (3, "Vertex Retail Co.", "Retail", 27_300_000, 46),
                (4, "Atlas Energy Partners", "Energy", 65_000_000, 84),
                (5, "Summit Financial", "Financial Services", 33_700_000, 69),
                (6, "Harbor Logistics", "Logistics", 21_900_000, 61),
            ]
            invoices = [
                (1, 1, 125_000, "overdue", today - timedelta(days=21)),
                (2, 1, 88_400, "paid", today - timedelta(days=45)),
                (3, 2, 240_000, "open", today + timedelta(days=14)),
                (4, 2, 73_500, "paid", today - timedelta(days=18)),
                (5, 3, 51_200, "open", today + timedelta(days=7)),
                (6, 4, 310_000, "overdue", today - timedelta(days=34)),
                (7, 4, 140_000, "open", today + timedelta(days=20)),
                (8, 5, 97_500, "open", today + timedelta(days=5)),
                (9, 5, 66_000, "overdue", today - timedelta(days=9)),
                (10, 6, 112_800, "paid", today - timedelta(days=30)),
            ]
            tickets = [
                (1, 1, "billing", "high", "open"),
                (2, 1, "integration", "medium", "open"),
                (3, 2, "authentication", "high", "open"),
                (4, 2, "reporting", "medium", "closed"),
                (5, 3, "workflow", "low", "open"),
                (6, 4, "integration", "critical", "open"),
                (7, 4, "escalation", "high", "open"),
                (8, 5, "compliance", "high", "open"),
                (9, 5, "billing", "medium", "closed"),
                (10, 6, "logistics", "medium", "open"),
            ]
            workflows = [
                (1, "Finance", "Invoice dispute triage", 7, 45, 120),
                (2, "Finance", "Payment status reporting", 5, 30, 90),
                (3, "Support", "Priority ticket routing", 6, 25, 260),
                (4, "Support", "Escalation summary drafting", 8, 40, 75),
                (5, "Operations", "Stock transfer approval", 9, 60, 110),
                (6, "Operations", "Vendor backorder follow-up", 6, 35, 140),
                (7, "Compliance", "Quarterly access review", 10, 120, 12),
                (8, "Customer Success", "Renewal risk review", 8, 55, 45),
            ]

            conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
            conn.executemany(
                "INSERT INTO invoices VALUES (?, ?, ?, ?, ?)",
                [(row_id, customer_id, amount, status, due.isoformat()) for row_id, customer_id, amount, status, due in invoices],
            )
            conn.executemany("INSERT INTO support_tickets VALUES (?, ?, ?, ?, ?)", tickets)
            conn.executemany("INSERT INTO workflows VALUES (?, ?, ?, ?, ?, ?)", workflows)
            existing = len(customers)

        if existing < SYNTHETIC_CUSTOMER_COUNT:
            max_customer_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM customers").fetchone()[0]
            max_invoice_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM invoices").fetchone()[0]
            max_ticket_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM support_tickets").fetchone()[0]
            max_workflow_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM workflows").fetchone()[0]
            synthetic = generate_synthetic_records(
                start_customer_id=max_customer_id + 1,
                start_invoice_id=max_invoice_id + 1,
                start_ticket_id=max_ticket_id + 1,
                start_workflow_id=max_workflow_id + 1,
                customer_count=SYNTHETIC_CUSTOMER_COUNT - existing,
            )
            conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", synthetic["customers"])
            conn.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?)", synthetic["invoices"])
            conn.executemany("INSERT INTO support_tickets VALUES (?, ?, ?, ?, ?)", synthetic["support_tickets"])
            conn.executemany("INSERT INTO workflows VALUES (?, ?, ?, ?, ?, ?)", synthetic["workflows"])


def execute_read_only_sql(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    """Run a SELECT query after blocking write or schema-changing SQL."""
    clean_sql = sql.strip()
    if not clean_sql.lower().startswith("select"):
        raise ValueError("Only read-only SELECT queries are allowed.")
    if FORBIDDEN_SQL.search(clean_sql):
        raise ValueError("Unsafe SQL rejected. DROP, DELETE, UPDATE, INSERT, ALTER, and related commands are not allowed.")

    with get_connection() as conn:
        conn.execute("PRAGMA query_only = ON")
        return conn.execute(clean_sql, params).fetchall()


def rows_to_markdown(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "No matching records found."
    headers = rows[0].keys()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def build_query(question: str) -> tuple[str, tuple[Any, ...], str]:
    normalized = question.lower()
    if FORBIDDEN_SQL.search(normalized):
        raise ValueError("Question appears to request a database write or schema change. This server is read-only.")

    if "overdue" in normalized and "invoice" in normalized:
        return (
            """
            SELECT c.name AS customer, i.amount, i.status, i.due_date
            FROM invoices i
            JOIN customers c ON c.id = i.customer_id
            WHERE i.status = 'overdue'
            ORDER BY i.amount DESC
            LIMIT 10
            """,
            (),
            "Overdue invoice exposure by customer:",
        )
    if ("open" in normalized and "invoice" in normalized) or "exposure" in normalized:
        return (
            """
            SELECT c.name AS customer, SUM(i.amount) AS open_invoice_amount
            FROM invoices i
            JOIN customers c ON c.id = i.customer_id
            WHERE i.status IN ('open', 'overdue')
            GROUP BY c.name
            ORDER BY open_invoice_amount DESC
            LIMIT 10
            """,
            (),
            "Open and overdue invoice exposure:",
        )
    if "risk" in normalized:
        return (
            "SELECT name, industry, annual_revenue, risk_score FROM customers ORDER BY risk_score DESC LIMIT 10",
            (),
            "Customers ranked by risk score:",
        )
    if "industry" in normalized or "revenue" in normalized:
        return (
            """
            SELECT industry, COUNT(*) AS customer_count, SUM(annual_revenue) AS total_annual_revenue
            FROM customers
            GROUP BY industry
            ORDER BY total_annual_revenue DESC
            """,
            (),
            "Revenue summarized by industry:",
        )
    if "ticket" in normalized or "support" in normalized:
        return (
            """
            SELECT c.name AS customer, t.issue_type, t.priority, t.status
            FROM support_tickets t
            JOIN customers c ON c.id = t.customer_id
            ORDER BY
                CASE t.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
                c.name
            LIMIT 10
            """,
            (),
            "Support tickets by priority:",
        )
    return (
        "SELECT name, industry, annual_revenue, risk_score FROM customers ORDER BY annual_revenue DESC",
        (),
        "I mapped the question to a customer summary because no more specific read-only pattern matched:",
    )


def document_snippets(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search local text files through a local vector index."""
    index = LocalVectorIndex(DOCUMENTS_DIR)
    return index.search(query, limit=limit)


@mcp.tool()
def query_business_database(question: str) -> str:
    """Answer a business question with generated read-only SQL over enterprise data."""
    try:
        sql, params, intro = build_query(question)
        rows = execute_read_only_sql(sql, params)
        return f"{intro}\n\nGenerated SQL:\n```sql\n{sql.strip()}\n```\n\n{rows_to_markdown(rows)}"
    except Exception as exc:
        return f"Could not answer the database question: {exc}"


@mcp.tool()
def generate_read_only_sql(question: str) -> str:
    """Generate SQL for a natural-language question and validate it with the read-only SQL guard."""
    try:
        sql, params, intro = generate_sql(question)
        execute_read_only_sql(sql, params)
        return f"{intro}\n\n```sql\n{sql.strip()}\n```"
    except Exception as exc:
        return f"SQL generation failed safety validation: {exc}"


@mcp.tool()
def search_documents(query: str) -> str:
    """Find relevant snippets from local enterprise text documents using local vector search."""
    try:
        snippets = document_snippets(query)
        if not snippets:
            return "No relevant document snippets found. Try a more specific business, customer, compliance, or workflow term."
        lines = ["Relevant local document snippets:"]
        for item in snippets:
            lines.append(f"\n- {item['document']} (score {item['score']}): {item['snippet']}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Document search failed: {exc}"


@mcp.tool()
def analyse_workflows(department: str | None = None) -> str:
    """Rank workflow automation candidates using manual effort, frequency, and estimated time savings."""
    try:
        sql = "SELECT * FROM workflows"
        params: tuple[Any, ...] = ()
        if department:
            sql += " WHERE lower(department) = lower(?)"
            params = (department,)
        rows = execute_read_only_sql(sql, params)
        if not rows:
            return f"No workflows found for department: {department}"

        df = pd.DataFrame([dict(row) for row in rows])
        df["monthly_manual_minutes"] = df["manual_steps"] * df["avg_time_minutes"] * df["frequency_per_month"]
        df["impact_score"] = (df["monthly_manual_minutes"] / 60).round(1)
        df["recommendation"] = df.apply(
            lambda row: (
                f"Automate '{row.process_name}' with rules, routing, and status updates; "
                f"estimated impact is {row.impact_score} manual hours/month."
            ),
            axis=1,
        )
        df = df.sort_values("impact_score", ascending=False)
        output = ["Automation recommendations ranked by impact:"]
        for rank, (_, row) in enumerate(df.iterrows(), start=1):
            output.append(
                f"\n{rank}. {row['department']} - {row['process_name']}\n"
                f"   Impact score: {row['impact_score']} hours/month\n"
                f"   Manual steps: {row['manual_steps']}; average time: {row['avg_time_minutes']} minutes; "
                f"frequency: {row['frequency_per_month']}/month\n"
                f"   Recommendation: {row['recommendation']}"
            )
        return "\n".join(output)
    except Exception as exc:
        return f"Workflow analysis failed: {exc}"


@mcp.tool()
def generate_risk_report(customer_name: str) -> str:
    """Combine customer risk, invoices, support tickets, and local document findings into one report."""
    try:
        customers = execute_read_only_sql(
            "SELECT * FROM customers WHERE lower(name) = lower(?)",
            (customer_name,),
        )
        if not customers:
            return f"No customer found named '{customer_name}'."
        customer = dict(customers[0])
        invoices = execute_read_only_sql(
            "SELECT amount, status, due_date FROM invoices WHERE customer_id = ? ORDER BY due_date",
            (customer["id"],),
        )
        tickets = execute_read_only_sql(
            "SELECT issue_type, priority, status FROM support_tickets WHERE customer_id = ? ORDER BY priority",
            (customer["id"],),
        )
        docs = document_snippets(customer["name"], limit=3)

        invoice_df = pd.DataFrame([dict(row) for row in invoices])
        open_exposure = 0.0
        overdue_exposure = 0.0
        if not invoice_df.empty:
            open_exposure = float(invoice_df[invoice_df["status"].isin(["open", "overdue"])]["amount"].sum())
            overdue_exposure = float(invoice_df[invoice_df["status"] == "overdue"]["amount"].sum())

        ticket_counts = Counter(row["status"] for row in tickets)
        high_priority_open = [
            dict(row)
            for row in tickets
            if row["status"] == "open" and row["priority"] in {"high", "critical"}
        ]
        risk_band = "High" if customer["risk_score"] >= 75 else "Medium" if customer["risk_score"] >= 50 else "Low"

        report = [
            f"# Risk Report: {customer['name']}",
            "",
            f"- Industry: {customer['industry']}",
            f"- Annual revenue: ${customer['annual_revenue']:,.0f}",
            f"- Risk score: {customer['risk_score']} ({risk_band})",
            f"- Open invoice exposure: ${open_exposure:,.0f}",
            f"- Overdue invoice exposure: ${overdue_exposure:,.0f}",
            f"- Support tickets: {dict(ticket_counts)}",
            f"- High-priority open tickets: {len(high_priority_open)}",
            "",
            "## Recommended Actions",
        ]
        if overdue_exposure:
            report.append("- Prioritize finance follow-up for overdue invoices and confirm dispute status.")
        if high_priority_open:
            report.append("- Escalate high-priority open support issues with named owners and target resolution dates.")
        if customer["risk_score"] >= 75:
            report.append("- Start executive-level retention review because the customer is in the high-risk band.")
        if not overdue_exposure and not high_priority_open:
            report.append("- Maintain normal account monitoring and review upcoming renewal signals.")

        report.extend(["", "## Document Findings"])
        if docs:
            for item in docs:
                report.append(f"- {item['document']}: {item['snippet']}")
        else:
            report.append("- No local document findings matched this customer.")

        return "\n".join(report)
    except Exception as exc:
        return f"Risk report generation failed: {exc}"


@mcp.tool()
def database_stats() -> str:
    """Show record counts for the seeded enterprise dataset."""
    try:
        rows = execute_read_only_sql(
            """
            SELECT 'customers' AS table_name, COUNT(*) AS record_count FROM customers
            UNION ALL
            SELECT 'invoices', COUNT(*) FROM invoices
            UNION ALL
            SELECT 'support_tickets', COUNT(*) FROM support_tickets
            UNION ALL
            SELECT 'workflows', COUNT(*) FROM workflows
            """
        )
        return "Enterprise dataset scale:\n\n" + rows_to_markdown(rows)
    except Exception as exc:
        return f"Database stats failed: {exc}"


@mcp.tool()
def run_agent_workflow(goal: str, customer_name: str | None = None, department: str | None = None) -> str:
    """Run a simple agent workflow that plans, calls tools, and composes an enterprise recommendation."""
    steps = [
        f"Goal: {goal}",
        "",
        "## Agent Plan",
        "1. Inspect relevant structured data.",
        "2. Retrieve document evidence.",
        "3. Analyse workflow automation impact.",
        "4. Combine findings into next actions.",
        "",
    ]

    if customer_name:
        steps.extend(["## Customer Risk", generate_risk_report(customer_name), ""])

    query = goal
    if customer_name:
        query += f" {customer_name}"
    steps.extend(["## Document Retrieval", search_documents(query), ""])

    workflow_department = department
    if not workflow_department:
        lowered = goal.lower()
        if "finance" in lowered:
            workflow_department = "Finance"
        elif "support" in lowered:
            workflow_department = "Support"
        elif "operation" in lowered:
            workflow_department = "Operations"

    steps.extend(["## Workflow Analysis", analyse_workflows(workflow_department), ""])
    steps.extend(
        [
            "## Agent Recommendation",
            "- Use the structured data to prioritize customers or departments with measurable exposure.",
            "- Use document findings as supporting evidence before automation or escalation decisions.",
            "- Start with the highest monthly manual-hour workflow because it has the clearest automation ROI.",
        ]
    )
    return "\n".join(steps)


seed_database()

if __name__ == "__main__":
    mcp.run()
