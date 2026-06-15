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

See the full project README at [`enterprise-mcp-agent/README.md`](enterprise-mcp-agent/README.md).
