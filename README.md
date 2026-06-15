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

## What It Does

- Exposes enterprise data from SQLite through MCP tools.
- Searches local business documents for relevant snippets.
- Uses Pandas to rank workflow automation opportunities.
- Generates customer risk reports by combining invoices, support tickets, customer risk scores, and document findings.
- Runs locally without external API calls.

## Example Inputs and Outputs

### 1. Query Business Database

Input:

```text
Show overdue invoices by customer
```

Output:

```text
Overdue invoice exposure by customer:

| customer | amount | status | due_date |
| --- | --- | --- | --- |
| Atlas Energy Partners | 310000.0 | overdue | 2026-05-08 |
| Acme Manufacturing | 125000.0 | overdue | 2026-05-21 |
| Summit Financial | 66000.0 | overdue | 2026-06-02 |
```

### 2. Search Documents

Input:

```text
invoice automation
```

Output:

```text
Relevant local document snippets:

- operations_review.txt (score 2): Finance teams spend the most time on invoice follow-up, dispute triage, and payment-status reporting. High-volume manual work is a strong candidate for automation when the work is frequent, rule-based, and tied to measurable cycle time.

- customer_success_notes.txt (score 1): Acme Manufacturing requested automated invoice reminders after two late payments in the last quarter. Their finance team cited manual reconciliation and missing purchase order references as recurring friction.
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
