"""Contact tools — calls VOSS API over HTTP."""

import json

from mcp_server.api_client import api_get, api_post, api_put
from mcp_server.helpers import contact_name, format_currency


_UPDATE_FIELDS = (
    "first_name", "last_name", "email", "phone", "role",
    "linkedin_url", "platform_handles", "urls",
    "company_name", "company_id",
    "tags", "notes", "segment", "engagement_stage",
    "inbound_channel", "do_not_contact",
)


def update_contact(
    contact_id: str,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    phone: str = "",
    role: str = "",
    linkedin_url: str = "",
    platform_handles: str = "",
    urls: str = "",
    company_name: str = "",
    company_id: str = "",
    tags: str = "",
    notes: str = "",
    segment: str = "",
    engagement_stage: str = "",
    inbound_channel: str = "",
    do_not_contact: str = "",
) -> str:
    """Update any structured field on an existing contact. company_name is
    resolved server-side and the company is created if it doesn't exist."""
    payload = {
        k: v for k, v in locals().items()
        if k in _UPDATE_FIELDS and v
    }
    if not payload:
        return "No fields to update."
    record = api_put(f"/api/contacts/{contact_id}", payload)
    name = contact_name(record)
    return f"Updated contact **{name}** (ID: {contact_id})."


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
    # The API dedups: a re-add of an existing person enriches that contact rather
    # than creating a duplicate. Report which happened so the agent doesn't claim
    # a new contact was created when it wasn't.
    verb = "Matched existing contact (enriched, not duplicated)" if record.get("deduped") else "Created contact"
    return (
        f"{verb} **{name}** (ID: {record['id']})"
        + (f" at {company_name}" if company_name else "")
        + "."
    )
