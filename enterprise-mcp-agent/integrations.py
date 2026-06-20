from __future__ import annotations

import os
from typing import Any

import requests


REQUEST_TIMEOUT = 15
DEFAULT_GITHUB_REPOSITORY = "Nikithaxx05/enterprise-mcp-agent"


def _format_dict(title: str, values: dict[str, Any]) -> str:
    lines = [title, ""]
    for key, value in values.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _demo_hubspot_customer(company_name: str) -> str:
    demo = {
        "source": "Demo fallback because HUBSPOT_ACCESS_TOKEN is not configured",
        "company": company_name,
        "lifecycle_stage": "Customer",
        "crm_owner": "Enterprise Success",
        "last_activity": "Renewal review and invoice follow-up",
        "crm_signal": "Executive sponsor active; finance approval is the main blocker",
    }
    return _format_dict("HubSpot customer record:", demo)


def get_hubspot_customer(company_name: str) -> str:
    """Fetch a company record from HubSpot CRM, or return a local demo record."""
    token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not token:
        return _demo_hubspot_customer(company_name)

    url = "https://api.hubapi.com/crm/v3/objects/companies/search"
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "name",
                        "operator": "CONTAINS_TOKEN",
                        "value": company_name,
                    }
                ]
            }
        ],
        "properties": ["name", "domain", "industry", "annualrevenue", "lifecyclestage", "hs_lastmodifieddate"],
        "limit": 3,
    }
    response = requests.post(url, headers=_headers(token), json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return f"No HubSpot company record found for '{company_name}'."

    lines = ["HubSpot customer records:"]
    for result in results:
        properties = result.get("properties", {})
        lines.append(
            "\n"
            + _format_dict(
                f"Company ID {result.get('id')}:",
                {
                    "name": properties.get("name"),
                    "domain": properties.get("domain"),
                    "industry": properties.get("industry"),
                    "annualrevenue": properties.get("annualrevenue"),
                    "lifecyclestage": properties.get("lifecyclestage"),
                    "last_modified": properties.get("hs_lastmodifieddate"),
                },
            )
        )
    return "\n".join(lines)


def _demo_jira_tickets(customer_name: str | None = None) -> str:
    customer = customer_name or "Atlas Energy Partners"
    tickets = [
        {
            "key": "ENT-1842",
            "customer": customer,
            "summary": "Critical integration outage blocking renewal validation",
            "priority": "Critical",
            "status": "In Progress",
        },
        {
            "key": "ENT-1881",
            "customer": customer,
            "summary": "Invoice dispute evidence requested by finance team",
            "priority": "High",
            "status": "Open",
        },
    ]
    lines = ["Open Jira tickets:", "", "Source: Demo fallback because JIRA_BASE_URL, JIRA_EMAIL, or JIRA_API_TOKEN is not configured"]
    for ticket in tickets:
        lines.append(
            f"\n- {ticket['key']} [{ticket['priority']} / {ticket['status']}]: "
            f"{ticket['summary']} ({ticket['customer']})"
        )
    return "\n".join(lines)


def get_open_jira_tickets(customer_name: str | None = None, priority: str | None = None) -> str:
    """Fetch open Jira tickets, optionally filtered by customer and priority."""
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    if not base_url or not email or not token:
        return _demo_jira_tickets(customer_name)

    jql_parts = ["statusCategory != Done"]
    if project_key:
        jql_parts.append(f"project = {project_key}")
    if customer_name:
        safe_customer = customer_name.replace('"', '\\"')
        jql_parts.append(f'text ~ "{safe_customer}"')
    if priority:
        safe_priority = priority.replace('"', '\\"')
        jql_parts.append(f'priority = "{safe_priority}"')
    jql = " AND ".join(jql_parts) + " ORDER BY priority DESC, updated DESC"

    response = requests.post(
        f"{base_url}/rest/api/3/search",
        auth=(email, token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"jql": jql, "maxResults": 10, "fields": ["summary", "priority", "status", "updated"]},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    issues = response.json().get("issues", [])
    if not issues:
        return "No matching open Jira tickets found."

    lines = [f"Open Jira tickets for JQL: `{jql}`"]
    for issue in issues:
        fields = issue.get("fields", {})
        priority_name = (fields.get("priority") or {}).get("name")
        status_name = (fields.get("status") or {}).get("name")
        lines.append(f"\n- {issue.get('key')} [{priority_name} / {status_name}]: {fields.get('summary')}")
    return "\n".join(lines)


def _github_get(path: str, token: str | None) -> Any:
    url = f"https://api.github.com{path}"
    response = requests.get(url, headers=_headers(token), timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def analyse_github_repository(owner_repo: str | None = None) -> str:
    """Analyse GitHub repository health using issues, pull requests, and contributors."""
    repository = owner_repo or os.getenv("GITHUB_REPOSITORY") or DEFAULT_GITHUB_REPOSITORY
    token = os.getenv("GITHUB_TOKEN")
    try:
        repo = _github_get(f"/repos/{repository}", token)
        issues = _github_get(f"/repos/{repository}/issues?state=open&per_page=100", token)
        pulls = _github_get(f"/repos/{repository}/pulls?state=open&per_page=100", token)
        contributors = _github_get(f"/repos/{repository}/contributors?per_page=100", token)
    except Exception as exc:
        return _format_dict(
            f"GitHub repository risk: {repository}",
            {
                "source": "Demo fallback because the live GitHub API could not be reached",
                "open_issues": "unknown",
                "open_pull_requests": "unknown",
                "contributors": "unknown",
                "repository_risk_score": "25 (Low demo estimate)",
                "recommendation": "Configure GITHUB_TOKEN and network access for live repository risk analysis",
                "error": exc,
            },
        )

    issue_count = len([issue for issue in issues if "pull_request" not in issue])
    pr_count = len(pulls)
    contributor_count = len(contributors)
    stale_issue_count = sum(1 for issue in issues if "bug" in [label.get("name", "").lower() for label in issue.get("labels", [])])
    risk_score = min(100, issue_count * 3 + pr_count * 4 + max(0, 5 - contributor_count) * 8 + stale_issue_count * 5)
    risk_band = "High" if risk_score >= 70 else "Medium" if risk_score >= 35 else "Low"

    return _format_dict(
        f"GitHub repository risk: {repository}",
        {
            "description": repo.get("description"),
            "default_branch": repo.get("default_branch"),
            "stars": repo.get("stargazers_count"),
            "open_issues": issue_count,
            "open_pull_requests": pr_count,
            "contributors": contributor_count,
            "bug_labeled_open_items": stale_issue_count,
            "repository_risk_score": f"{risk_score} ({risk_band})",
            "recommendation": "Review open issues and PRs before demoing if risk is Medium or High",
        },
    )
