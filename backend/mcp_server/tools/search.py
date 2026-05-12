"""Unified VOSS search — knowledge-base style across all entity types."""

from mcp_server.api_client import api_get
from mcp_server.helpers import format_currency


def search(query: str) -> str:
    if not query.strip():
        return "Provide a search query."

    result = api_get("/api/search", {"q": query})
    total = result.get("total", 0)
    if total == 0:
        return f"No VOSS records reference '{query}'."

    lines = [f"Found {total} record(s) referencing '{query}':\n"]

    companies = result.get("companies") or []
    if companies:
        lines.append(f"## Companies ({len(companies)})")
        for c in companies:
            extra = f" — {c['industry']}" if c.get("industry") else ""
            lines.append(f"- **{c.get('name', '(unnamed)')}**{extra} (ID: {c['id']})")
        lines.append("")

    contacts = result.get("contacts") or []
    if contacts:
        lines.append(f"## Contacts ({len(contacts)})")
        for c in contacts:
            role = f" — {c['role']}" if c.get("role") else ""
            company = f" at {c['company_name']}" if c.get("company_name") else ""
            lines.append(f"- **{c.get('name', '(unnamed)')}**{role}{company} (ID: {c['id']})")
        lines.append("")

    deals = result.get("deals") or []
    if deals:
        lines.append(f"## Deals ({len(deals)})")
        for d in deals:
            stage = f"[{d['stage'].upper()}] " if d.get("stage") else ""
            value = ""
            if d.get("value"):
                value = f" — {format_currency(d['value'], d.get('currency', 'GBP'))}"
            ctx_parts = [p for p in (d.get("contact_name"), d.get("company_name")) if p]
            ctx = f" ({' / '.join(ctx_parts)})" if ctx_parts else ""
            lines.append(f"- {stage}{d.get('title', 'Untitled')}{value}{ctx} (ID: {d['id']})")
        lines.append("")

    interactions = result.get("interactions") or []
    if interactions:
        lines.append(f"## Interactions ({len(interactions)})")
        for i in interactions:
            date = (i.get("occurred_at") or i.get("created_at") or "")[:10]
            itype = (i.get("type") or "note").upper()
            ctx_parts = [p for p in (i.get("contact_name"), i.get("company_name")) if p]
            ctx = f" — {' at '.join(ctx_parts)}" if ctx_parts else ""
            subj = i.get("subject") or "(no subject)"
            lines.append(f"- {date} {itype}: {subj}{ctx} (ID: {i['id']})")
        lines.append("")

    follow_ups = result.get("follow_ups") or []
    if follow_ups:
        lines.append(f"## Follow-ups ({len(follow_ups)})")
        for f in follow_ups:
            due = f.get("due_date", "no date")
            if f.get("due_time"):
                due += f" {f['due_time']}"
            status = f"[{(f.get('status') or 'pending').upper()}] "
            ctx_parts = [p for p in (f.get("contact_name"), f.get("company_name")) if p]
            ctx = f" — {' at '.join(ctx_parts)}" if ctx_parts else ""
            lines.append(f"- {status}{f.get('title', 'Untitled')} — due {due}{ctx} (ID: {f['id']})")
        lines.append("")

    return "\n".join(lines).rstrip()
