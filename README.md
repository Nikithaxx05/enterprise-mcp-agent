# enterprise-mcp-agent

This repository contains a Python Model Context Protocol (MCP) server for enterprise business data, document search, workflow analysis, and customer risk reporting.

The project code lives in [`enterprise-mcp-agent/`](enterprise-mcp-agent/).

## Quick Start

```bash
cd enterprise-mcp-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -c "import server; print(server.generate_risk_report('Atlas Energy Partners'))"
```

Run the dashboard:

```bash
streamlit run dashboard.py
```

## What It Does

- Exposes enterprise data from SQLite through MCP tools.
- Generates safe read-only SQL from natural-language questions.
- Searches local business documents with a local vector-style index.
- Uses Pandas to rank workflow automation opportunities.
- Generates customer risk reports by combining invoices, support tickets, customer risk scores, and document findings.
- Seeds a 50k+ synthetic enterprise dataset for realistic scale testing.
- Includes a Streamlit dashboard for browsing metrics and automation opportunities.
- Includes an agent workflow that chains database, document, workflow, and risk-analysis tools.
- Adds optional HubSpot, Jira, and GitHub API tools for CRM, ticket, and repository-risk context.
- Adds a guarded Jira issue creation tool with dry-run previews by default.
- Runs locally without external API calls.

## Current Dataset Scale

```text
| table_name | record_count |
| --- | --- |
| customers | 50000 |
| invoices | 60010 |
| support_tickets | 40010 |
| workflows | 508 |
```

## Example Inputs and Outputs

### 1. Query Business Database

Input:

```text
Show overdue invoices by customer
```

Output:

````text
Overdue invoice exposure by customer:

Generated SQL:
```sql
SELECT c.name AS customer, i.amount, i.status, i.due_date
FROM invoices i
JOIN customers c ON c.id = i.customer_id
WHERE i.status = 'overdue'
ORDER BY i.amount DESC
LIMIT 10
```

| customer | amount | status | due_date |
| --- | --- | --- | --- |
| Atlas Energy Partners | 310000.0 | overdue | 2026-05-08 |
| Northstar Networks 17437 | 239974.0 | overdue | 2026-04-19 |
| Northstar Logistics 12877 | 239965.0 | overdue | 2026-05-01 |
| BluePeak Networks 14938 | 239958.0 | overdue | 2026-04-20 |
| Cedar Networks 34639 | 239948.0 | overdue | 2026-06-06 |
````

### 2. Search Documents

Input:

```text
invoice automation
```

Output:

```text
Relevant local document snippets:

- operations_review.txt (score 0.185): Finance teams spend the most time on invoice follow-up, dispute triage, and payment-status reporting. High-volume manual work is a strong candidate for automation when the work is frequent, rule-based, and tied to measurable cycle time.

- operations_review.txt (score 0.165): Operations teams identified approval workflows, monthly reporting, and vendor coordination as repeatable processes with high automation potential.
```

### 3. Analyse Workflows

Input:

```text
Finance
```

Output:

```text
Automation recommendations ranked by impact:

1. Finance - Invoice dispute triage
   Impact score: 630.0 hours/month
   Manual steps: 7; average time: 45 minutes; frequency: 120/month
   Recommendation: Automate 'Invoice dispute triage' with rules, routing, and status updates; estimated impact is 630.0 manual hours/month.

2. Finance - Payment status reporting
   Impact score: 225.0 hours/month
   Manual steps: 5; average time: 30 minutes; frequency: 90/month
   Recommendation: Automate 'Payment status reporting' with rules, routing, and status updates; estimated impact is 225.0 manual hours/month.
```

### 4. Generate Risk Report

Input:

```text
Atlas Energy Partners
```

Output:

```text
# Risk Report: Atlas Energy Partners

- Industry: Energy
- Annual revenue: $65,000,000
- Risk score: 84 (High)
- Open invoice exposure: $450,000
- Overdue invoice exposure: $310,000
- Support tickets: {'open': 2}
- High-priority open tickets: 2

## Recommended Actions
- Prioritize finance follow-up for overdue invoices and confirm dispute status.
- Escalate high-priority open support issues with named owners and target resolution dates.
- Start executive-level retention review because the customer is in the high-risk band.

## Document Findings
- customer_success_notes.txt: Atlas Energy Partners is under renewal review. Account notes mention aging unpaid invoices, field-service integration delays, and a request for clearer incident escalation reporting.
- security_and_compliance.txt: Atlas Energy Partners flagged vendor risk concerns related to delayed integrations and inconsistent escalation notes.
```

See the full project README at [`enterprise-mcp-agent/README.md`](enterprise-mcp-agent/README.md).
