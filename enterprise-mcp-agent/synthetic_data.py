from __future__ import annotations

from datetime import date, timedelta
from random import Random


INDUSTRIES = [
    "Manufacturing",
    "Healthcare",
    "Retail",
    "Energy",
    "Financial Services",
    "Logistics",
    "Technology",
    "Telecommunications",
]

COMPANY_PREFIXES = [
    "Northstar",
    "BluePeak",
    "Cedar",
    "IronGate",
    "Clearwater",
    "Evergreen",
    "Redwood",
    "Silverline",
    "BrightPath",
    "Summit",
]

COMPANY_SUFFIXES = [
    "Systems",
    "Holdings",
    "Industries",
    "Networks",
    "Partners",
    "Labs",
    "Group",
    "Logistics",
    "Analytics",
    "Enterprises",
]

INVOICE_STATUSES = ["paid", "open", "overdue"]
ISSUE_TYPES = ["billing", "integration", "authentication", "reporting", "workflow", "compliance", "data quality"]
PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_STATUSES = ["open", "closed", "pending"]
DEPARTMENTS = ["Finance", "Support", "Operations", "Compliance", "Customer Success", "Sales"]
PROCESS_NAMES = [
    "Invoice dispute triage",
    "Payment status reporting",
    "Priority ticket routing",
    "Renewal risk review",
    "Vendor coordination",
    "Access review",
    "Contract approval",
    "Escalation summary drafting",
]


def generate_synthetic_records(
    start_customer_id: int,
    start_invoice_id: int,
    start_ticket_id: int,
    start_workflow_id: int,
    customer_count: int = 50_000,
    invoice_count: int = 60_000,
    ticket_count: int = 40_000,
    workflow_count: int = 500,
) -> dict[str, list[tuple]]:
    """Generate deterministic fake enterprise data at 50k+ record scale."""
    rng = Random(42)
    today = date.today()

    customers = []
    for offset in range(customer_count):
        customer_id = start_customer_id + offset
        prefix = COMPANY_PREFIXES[offset % len(COMPANY_PREFIXES)]
        suffix = COMPANY_SUFFIXES[(offset // len(COMPANY_PREFIXES)) % len(COMPANY_SUFFIXES)]
        industry = INDUSTRIES[offset % len(INDUSTRIES)]
        revenue = rng.randint(1_000_000, 95_000_000)
        risk_score = rng.randint(18, 92)
        customers.append((customer_id, f"{prefix} {suffix} {customer_id}", industry, revenue, risk_score))

    invoices = []
    for offset in range(invoice_count):
        invoice_id = start_invoice_id + offset
        customer_id = start_customer_id + rng.randrange(customer_count)
        status = INVOICE_STATUSES[rng.randrange(len(INVOICE_STATUSES))]
        amount = rng.randint(2_500, 240_000)
        due_offset = rng.randint(-75, 60)
        if status == "overdue":
            due_offset = -rng.randint(1, 75)
        invoices.append((invoice_id, customer_id, amount, status, (today + timedelta(days=due_offset)).isoformat()))

    tickets = []
    for offset in range(ticket_count):
        ticket_id = start_ticket_id + offset
        customer_id = start_customer_id + rng.randrange(customer_count)
        issue_type = ISSUE_TYPES[rng.randrange(len(ISSUE_TYPES))]
        priority = PRIORITIES[rng.randrange(len(PRIORITIES))]
        status = TICKET_STATUSES[rng.randrange(len(TICKET_STATUSES))]
        tickets.append((ticket_id, customer_id, issue_type, priority, status))

    workflows = []
    for offset in range(workflow_count):
        workflow_id = start_workflow_id + offset
        department = DEPARTMENTS[offset % len(DEPARTMENTS)]
        process_name = PROCESS_NAMES[offset % len(PROCESS_NAMES)]
        manual_steps = rng.randint(3, 14)
        avg_time_minutes = rng.randint(10, 120)
        frequency_per_month = rng.randint(8, 320)
        workflows.append((workflow_id, department, process_name, manual_steps, avg_time_minutes, frequency_per_month))

    return {
        "customers": customers,
        "invoices": invoices,
        "support_tickets": tickets,
        "workflows": workflows,
    }
