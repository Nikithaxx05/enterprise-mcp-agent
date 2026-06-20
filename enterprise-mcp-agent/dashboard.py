from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "enterprise.db"


def read_table(table_name: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


st.set_page_config(page_title="Enterprise MCP Agent", layout="wide")
st.title("Enterprise MCP Agent Dashboard")

customers = read_table("customers")
invoices = read_table("invoices")
tickets = read_table("support_tickets")
workflows = read_table("workflows")

metric_cols = st.columns(4)
metric_cols[0].metric("Customers", f"{len(customers):,}")
metric_cols[1].metric("Invoices", f"{len(invoices):,}")
metric_cols[2].metric("Support Tickets", f"{len(tickets):,}")
metric_cols[3].metric("Workflows", f"{len(workflows):,}")

st.subheader("Risk and Revenue")
left, right = st.columns(2)
with left:
    st.bar_chart(customers.groupby("industry")["annual_revenue"].sum().sort_values(ascending=False))
with right:
    st.dataframe(customers.sort_values("risk_score", ascending=False).head(20), use_container_width=True)

st.subheader("Invoice Exposure")
invoice_summary = invoices.groupby("status")["amount"].sum().sort_values(ascending=False)
st.bar_chart(invoice_summary)

st.subheader("Workflow Automation Candidates")
workflow_df = workflows.copy()
workflow_df["monthly_manual_hours"] = (
    workflow_df["manual_steps"] * workflow_df["avg_time_minutes"] * workflow_df["frequency_per_month"] / 60
)
st.dataframe(
    workflow_df.sort_values("monthly_manual_hours", ascending=False).head(25),
    use_container_width=True,
)
