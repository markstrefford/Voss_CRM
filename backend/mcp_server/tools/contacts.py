"""Contact tools for the MCP server."""

from app.services.sheet_service import (
    contacts_sheet,
    companies_sheet,
    deals_sheet,
    interactions_sheet,
    follow_ups_sheet,
)
from mcp_server.helpers import resolve_company_name, format_currency


def search_contacts(query: str) -> str:
    """Search contacts by name, email, company, role, or tags.

    Args:
        query: Search term to match against contact fields
    """
    results = contacts_sheet.search(
        query,
        ["first_name", "last_name", "email", "phone", "role", "tags", "notes",
         "segment", "engagement_stage"],
    )
    # Also search by company name
    companies = companies_sheet.search(query, ["name"])
    if companies:
        company_ids = {c["id"] for c in companies}
        company_matches = [
            c for c in contacts_sheet.get_all()
            if c.get("company_id") in company_ids
            and c["id"] not in {r["id"] for r in results}
        ]
        results.extend(company_matches)

    if not results:
        return f"No contacts found for '{query}'."

    lines = [f"Found {len(results)} contact(s) for '{query}':\n"]
    for c in results:
        company = resolve_company_name(c.get("company_id", ""))
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        parts = [f"- **{name}** (ID: {c['id']})"]
        if c.get("role"):
            parts.append(f"  Role: {c['role']}")
        if company:
            parts.append(f"  Company: {company}")
        if c.get("email"):
            parts.append(f"  Email: {c['email']}")
        if c.get("phone"):
            parts.append(f"  Phone: {c['phone']}")
        if c.get("tags"):
            parts.append(f"  Tags: {c['tags']}")
        lines.append("\n".join(parts))
    return "\n".join(lines)


def get_contact_details(contact_id: str) -> str:
    """Get full profile for a contact including interactions, deals, and follow-ups.

    Args:
        contact_id: The contact's unique ID
    """
    contact = contacts_sheet.get_by_id(contact_id)
    if not contact:
        return f"Contact '{contact_id}' not found."

    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    company = resolve_company_name(contact.get("company_id", ""))

    lines = [f"# {name}"]
    if contact.get("role") or company:
        role_line = contact.get("role", "")
        if company:
            role_line = f"{role_line} at {company}" if role_line else company
        lines.append(role_line)
    lines.append("")

    # Contact info
    info = []
    if contact.get("email"):
        info.append(f"- Email: {contact['email']}")
    if contact.get("phone"):
        info.append(f"- Phone: {contact['phone']}")
    if contact.get("linkedin_url"):
        info.append(f"- LinkedIn: {contact['linkedin_url']}")
    if contact.get("source"):
        info.append(f"- Source: {contact['source']}")
    if contact.get("tags"):
        info.append(f"- Tags: {contact['tags']}")
    if contact.get("status"):
        info.append(f"- Status: {contact['status']}")
    if contact.get("segment"):
        info.append(f"- Segment: {contact['segment']}")
    if contact.get("engagement_stage"):
        info.append(f"- Engagement Stage: {contact['engagement_stage']}")
    if contact.get("inbound_channel"):
        info.append(f"- Inbound Channel: {contact['inbound_channel']}")
    if contact.get("do_not_contact") and contact["do_not_contact"].lower() == "true":
        info.append(f"- Do Not Contact: YES")
    if contact.get("campaign_id"):
        info.append(f"- Campaign ID: {contact['campaign_id']}")
    if contact.get("notes"):
        info.append(f"- Notes: {contact['notes']}")
    if info:
        lines.append("## Contact Info")
        lines.extend(info)
        lines.append("")

    # Deals
    deals = [d for d in deals_sheet.get_all() if d.get("contact_id") == contact_id]
    if deals:
        lines.append(f"## Deals ({len(deals)})")
        for d in deals:
            val = format_currency(d.get("value", "0"))
            lines.append(
                f"- [{d.get('stage', '').upper()}] {d.get('title', 'Untitled')} "
                f"— {val} (ID: {d['id']})"
            )
        lines.append("")

    # Follow-ups
    fups = [f for f in follow_ups_sheet.get_all() if f.get("contact_id") == contact_id]
    pending = [f for f in fups if f.get("status") == "pending"]
    if pending:
        lines.append(f"## Pending Follow-ups ({len(pending)})")
        for f in pending:
            due = f.get("due_date", "no date")
            if f.get("due_time"):
                due += f" {f['due_time']}"
            lines.append(f"- {f.get('title', 'Untitled')} — due {due} (ID: {f['id']})")
        lines.append("")

    # Recent interactions (last 10)
    ints = [
        i for i in interactions_sheet.get_all()
        if i.get("contact_id") == contact_id
    ]
    ints.sort(key=lambda x: x.get("occurred_at", x.get("created_at", "")), reverse=True)
    ints = ints[:10]
    if ints:
        lines.append(f"## Recent Interactions (last {len(ints)})")
        for i in ints:
            date = (i.get("occurred_at") or i.get("created_at", ""))[:10]
            direction = f" [{i.get('direction')}]" if i.get("direction") else ""
            itype = i.get("type", "note").upper()
            lines.append(f"- {date} {itype}{direction}: {i.get('subject', '(no subject)')}")
            if i.get("body"):
                # Truncate long bodies
                body = i["body"][:200]
                if len(i["body"]) > 200:
                    body += "..."
                lines.append(f"  {body}")
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
    """Create a new contact in the CRM.

    Args:
        first_name: Contact's first name (required)
        last_name: Contact's last name
        email: Email address
        phone: Phone number
        role: Job title or role
        company_name: Company name (will find or create the company)
        source: How this contact was found (e.g. referral, linkedin, conference)
        tags: Comma-separated tags
        notes: Any notes about this contact
        segment: Business segment (signal_strata, consulting, pe, other)
        engagement_stage: Relationship stage (new, nurturing, active, client, churned)
        inbound_channel: Where contact came from (linkedin, referral, conference, cold_outbound, website, other)
    """
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "role": role,
        "source": source,
        "tags": tags,
        "notes": notes,
        "status": "active",
        "segment": segment,
        "engagement_stage": engagement_stage,
        "inbound_channel": inbound_channel,
    }

    # Resolve company
    if company_name:
        companies = companies_sheet.search(company_name, ["name"])
        if companies:
            data["company_id"] = companies[0]["id"]
        else:
            new_company = companies_sheet.create({"name": company_name})
            data["company_id"] = new_company["id"]

    record = contacts_sheet.create(data)
    name = f"{first_name} {last_name}".strip()
    return (
        f"Created contact **{name}** (ID: {record['id']})"
        + (f" at {company_name}" if company_name else "")
        + "."
    )
