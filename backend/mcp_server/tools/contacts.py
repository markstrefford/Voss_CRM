"""Contact tools — calls VOSS API over HTTP."""

import json

from mcp_server.api_client import api_get, api_post
from mcp_server.helpers import contact_name, format_currency


def search_contacts(query: str) -> str:
    results = api_get("/api/contacts", {"q": query})
    if not results:
        return f"No contacts found for '{query}'."

    lines = [f"Found {len(results)} contact(s) for '{query}':\n"]
    for c in results:
        name = contact_name(c)
        parts = [f"- **{name}** (ID: {c['id']})"]
        if c.get("role"):
            parts.append(f"  Role: {c['role']}")
        if c.get("company_name"):
            parts.append(f"  Company: {c['company_name']}")
        if c.get("email"):
            parts.append(f"  Email: {c['email']}")
        if c.get("phone"):
            parts.append(f"  Phone: {c['phone']}")
        if c.get("tags"):
            parts.append(f"  Tags: {c['tags']}")
        lines.append("\n".join(parts))
    return "\n".join(lines)


def get_contact_details(contact_id: str) -> str:
    contact = api_get(f"/api/contacts/{contact_id}")
    name = contact_name(contact)

    lines = [f"# {name}"]
    if contact.get("role") or contact.get("company_name"):
        role_line = contact.get("role", "")
        if contact.get("company_name"):
            role_line = f"{role_line} at {contact['company_name']}" if role_line else contact["company_name"]
        lines.append(role_line)
    lines.append("")

    info = []
    for field, label in [
        ("email", "Email"), ("phone", "Phone"), ("linkedin_url", "LinkedIn"),
        ("source", "Source"), ("tags", "Tags"), ("segment", "Segment"),
        ("engagement_stage", "Engagement Stage"), ("notes", "Notes"),
    ]:
        if contact.get(field):
            info.append(f"- {label}: {contact[field]}")
    if info:
        lines.append("## Contact Info")
        lines.extend(info)
        lines.append("")

    # Deals for this contact
    deals = api_get("/api/deals", {"contact_id": contact_id})
    if deals:
        lines.append(f"## Deals ({len(deals)})")
        for d in deals:
            val = format_currency(d.get("value", "0"), d.get("currency", "GBP"))
            lines.append(
                f"- [{d.get('stage', '').upper()}] {d.get('title', 'Untitled')} "
                f"— {val} (ID: {d['id']})"
            )
        lines.append("")

    # Follow-ups for this contact
    fups = api_get("/api/follow-ups", {"contact_id": contact_id, "status": "pending"})
    if fups:
        lines.append(f"## Pending Follow-ups ({len(fups)})")
        for f in fups:
            due = f.get("due_date", "no date")
            if f.get("due_time"):
                due += f" {f['due_time']}"
            lines.append(f"- {f.get('title', 'Untitled')} — due {due} (ID: {f['id']})")
        lines.append("")

    # Recent interactions
    interactions = api_get("/api/interactions", {"contact_id": contact_id, "limit": "10"})
    if interactions:
        lines.append(f"## Recent Interactions (last {len(interactions)})")
        for i in interactions:
            date = (i.get("occurred_at") or i.get("created_at", ""))[:10]
            direction = f" [{i.get('direction')}]" if i.get("direction") else ""
            itype = i.get("type", "note").upper()
            lines.append(f"- {date} {itype}{direction}: {i.get('subject', '(no subject)')}")
        lines.append("")

    lines.append(f"_Contact ID: {contact_id} | Created: {contact.get('created_at', 'N/A')[:10]}_")
    return "\n".join(lines)


def create_contact(
    first_name: str,
    last_name: str = "",
    email: str = "",
    phone: str = "",
    role: str = "",
    company_name: str = "",
    source: str = "",
    tags: str = "",
    notes: str = "",
    segment: str = "",
    engagement_stage: str = "new",
    inbound_channel: str = "",
) -> str:
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "role": role,
        "company_name": company_name,
        "source": source,
        "tags": tags,
        "notes": notes,
        "segment": segment,
        "engagement_stage": engagement_stage,
        "inbound_channel": inbound_channel,
    }
    # Remove empty values
    data = {k: v for k, v in data.items() if v}
    data["first_name"] = first_name  # always required

    record = api_post("/api/contacts", data)
    name = f"{first_name} {last_name}".strip()
    return (
        f"Created contact **{name}** (ID: {record['id']})"
        + (f" at {company_name}" if company_name else "")
        + "."
    )
