"""Deal tools for the MCP server."""

from app.services.sheet_service import deals_sheet, interactions_sheet, contacts_sheet, companies_sheet
from mcp_server.helpers import resolve_contact_name, resolve_company_name, format_currency

VALID_STAGES = ["lead", "prospect", "qualified", "proposal", "negotiation", "won", "lost"]
VALID_PRIORITIES = ["low", "medium", "high"]


def get_pipeline() -> str:
    """Get an overview of all deals grouped by stage with values."""
    deals = deals_sheet.get_all()

    lines = ["# Deal Pipeline\n"]
    total_active_value = 0.0
    total_active_count = 0

    for stage in VALID_STAGES:
        stage_deals = [d for d in deals if d.get("stage") == stage]
        stage_value = sum(float(d.get("value") or 0) for d in stage_deals)

        if stage not in ("won", "lost"):
            total_active_value += stage_value
            total_active_count += len(stage_deals)

        if not stage_deals:
            lines.append(f"**{stage.upper()}** — 0 deals\n")
            continue

        lines.append(f"**{stage.upper()}** — {len(stage_deals)} deal(s), {format_currency(str(stage_value))}\n")
        for d in stage_deals:
            contact = resolve_contact_name(d.get("contact_id", ""))
            val = format_currency(d.get("value", "0"))
            lines.append(f"  - {d.get('title', 'Untitled')} — {val} ({contact}) [ID: {d['id']}]")
        lines.append("")

    lines.append(f"---\n**Active pipeline**: {total_active_count} deals, {format_currency(str(total_active_value))}")
    lines.append(f"**Total deals**: {len(deals)}")
    return "\n".join(lines)


def get_deal(deal_id: str) -> str:
    """Get full details about a specific deal.

    Args:
        deal_id: The deal's unique ID
    """
    deal = deals_sheet.get_by_id(deal_id)
    if not deal:
        return f"Deal '{deal_id}' not found."

    contact = resolve_contact_name(deal.get("contact_id", ""))
    company = resolve_company_name(deal.get("company_id", ""))

    lines = [f"# {deal.get('title', 'Untitled Deal')}"]
    lines.append(f"**Stage**: {deal.get('stage', 'N/A').upper()}")
    lines.append(f"**Value**: {format_currency(deal.get('value', '0'))}")
    if deal.get("currency") and deal["currency"] != "USD":
        lines.append(f"**Currency**: {deal['currency']}")
    if deal.get("priority"):
        lines.append(f"**Priority**: {deal['priority']}")
    lines.append(f"**Contact**: {contact}")
    if company:
        lines.append(f"**Company**: {company}")
    if deal.get("expected_close"):
        lines.append(f"**Expected close**: {deal['expected_close']}")
    if deal.get("notes"):
        lines.append(f"**Notes**: {deal['notes']}")
    lines.append("")

    # Recent interactions for this deal
    ints = [i for i in interactions_sheet.get_all() if i.get("deal_id") == deal_id]
    ints.sort(key=lambda x: x.get("occurred_at", x.get("created_at", "")), reverse=True)
    if ints:
        lines.append(f"## Recent Activity ({len(ints[:5])} of {len(ints)})")
        for i in ints[:5]:
            date = (i.get("occurred_at") or i.get("created_at", ""))[:10]
            lines.append(f"- {date} {i.get('type', 'note').upper()}: {i.get('subject', '(no subject)')}")
        lines.append("")

    lines.append(
        f"_Deal ID: {deal_id} | Created: {deal.get('created_at', 'N/A')[:10]} "
        f"| Updated: {deal.get('updated_at', 'N/A')[:10]}_"
    )
    return "\n".join(lines)


def update_deal_stage(deal_id: str, stage: str) -> str:
    """Move a deal to a new pipeline stage.

    Args:
        deal_id: The deal's unique ID
        stage: New stage — one of: lead, prospect, qualified, proposal, negotiation, won, lost
    """
    stage = stage.lower().strip()
    if stage not in VALID_STAGES:
        return f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"

    deal = deals_sheet.get_by_id(deal_id)
    if not deal:
        return f"Deal '{deal_id}' not found."

    old_stage = deal.get("stage", "unknown")
    updated = deals_sheet.update(deal_id, {"stage": stage})
    if not updated:
        return f"Failed to update deal '{deal_id}'."

    return (
        f"Moved **{deal.get('title', 'Untitled')}** from "
        f"{old_stage.upper()} → {stage.upper()}."
    )


def _resolve_name_to_id(name: str, kind: str) -> str:
    """Resolve a contact or company name to an ID. Returns ID or empty string."""
    if not name:
        return ""
    if kind == "contact":
        results = contacts_sheet.search(name, ["first_name", "last_name"])
        return results[0]["id"] if results else ""
    else:
        results = companies_sheet.search(name, ["name"])
        return results[0]["id"] if results else ""


def create_deal(
    title: str,
    contact_name: str = "",
    company_name: str = "",
    stage: str = "lead",
    value: str = "",
    currency: str = "GBP",
    priority: str = "medium",
    expected_close: str = "",
    notes: str = "",
) -> str:
    """Create a new deal in the CRM.

    Args:
        title: Deal title (required)
        contact_name: Name of the associated contact (will search to find match)
        company_name: Name of the associated company (will search to find match)
        stage: Pipeline stage — one of: lead, prospect, qualified, proposal, negotiation, won, lost
        value: Deal monetary value
        currency: Currency code (GBP, USD, EUR)
        priority: Deal priority — low, medium, or high
        expected_close: Expected close date (YYYY-MM-DD)
        notes: Any notes about this deal
    """
    stage = stage.lower().strip()
    if stage not in VALID_STAGES:
        return f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"

    priority = priority.lower().strip()
    if priority not in VALID_PRIORITIES:
        return f"Invalid priority '{priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}"

    data: dict = {
        "title": title,
        "stage": stage,
        "value": value,
        "currency": currency,
        "priority": priority,
        "expected_close": expected_close,
        "notes": notes,
    }

    contact_id = _resolve_name_to_id(contact_name, "contact")
    if contact_name and not contact_id:
        return f"Could not find a contact matching '{contact_name}'."
    if contact_id:
        data["contact_id"] = contact_id

    company_id = _resolve_name_to_id(company_name, "company")
    if company_name and not company_id:
        return f"Could not find a company matching '{company_name}'."
    if company_id:
        data["company_id"] = company_id

    record = deals_sheet.create(data)
    return (
        f"Created deal **{title}** (ID: {record['id']})"
        + (f" — {resolve_contact_name(contact_id)}" if contact_id else "")
        + (f" at {resolve_company_name(company_id)}" if company_id else "")
        + f" [{stage.upper()}]."
    )


def promote_contact_to_deal(
    contact_name: str,
    title: str,
    stage: str = "lead",
    value: str = "",
    currency: str = "GBP",
    priority: str = "medium",
    notes: str = "",
) -> str:
    """Create a deal from a contact, automatically resolving their company.

    Args:
        contact_name: Name of the contact (will search to find match)
        title: Deal title (required)
        stage: Pipeline stage — one of: lead, prospect, qualified, proposal, negotiation, won, lost
        value: Deal monetary value
        currency: Currency code (GBP, USD, EUR)
        priority: Deal priority — low, medium, or high
        notes: Any notes about this deal
    """
    contact_id = _resolve_name_to_id(contact_name, "contact")
    if not contact_id:
        return f"Could not find a contact matching '{contact_name}'."

    contact = contacts_sheet.get_by_id(contact_id)
    company_id = contact.get("company_id", "") if contact else ""

    stage = stage.lower().strip()
    if stage not in VALID_STAGES:
        return f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"

    priority = priority.lower().strip()
    if priority not in VALID_PRIORITIES:
        return f"Invalid priority '{priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}"

    data: dict = {
        "title": title,
        "contact_id": contact_id,
        "stage": stage,
        "value": value,
        "currency": currency,
        "priority": priority,
        "notes": notes,
    }
    if company_id:
        data["company_id"] = company_id

    record = deals_sheet.create(data)
    contact_display = resolve_contact_name(contact_id)
    company_display = resolve_company_name(company_id) if company_id else ""

    return (
        f"Created deal **{title}** (ID: {record['id']})"
        f" — {contact_display}"
        + (f" at {company_display}" if company_display else "")
        + f" [{stage.upper()}]."
    )


def update_deal(
    deal_id: str,
    title: str = "",
    contact_name: str = "",
    company_name: str = "",
    stage: str = "",
    value: str = "",
    currency: str = "",
    priority: str = "",
    expected_close: str = "",
    notes: str = "",
) -> str:
    """Update an existing deal. Only provided fields will be changed.

    Args:
        deal_id: The deal's unique ID (required)
        title: New deal title
        contact_name: Name of the associated contact (will search to find match)
        company_name: Name of the associated company (will search to find match)
        stage: New pipeline stage — one of: lead, prospect, qualified, proposal, negotiation, won, lost
        value: New deal monetary value
        currency: Currency code (GBP, USD, EUR)
        priority: Deal priority — low, medium, or high
        expected_close: Expected close date (YYYY-MM-DD)
        notes: Updated notes
    """
    deal = deals_sheet.get_by_id(deal_id)
    if not deal:
        return f"Deal '{deal_id}' not found."

    data: dict = {}

    if title:
        data["title"] = title
    if stage:
        stage = stage.lower().strip()
        if stage not in VALID_STAGES:
            return f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"
        data["stage"] = stage
    if value:
        data["value"] = value
    if currency:
        data["currency"] = currency
    if priority:
        priority = priority.lower().strip()
        if priority not in VALID_PRIORITIES:
            return f"Invalid priority '{priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}"
        data["priority"] = priority
    if expected_close:
        data["expected_close"] = expected_close
    if notes:
        data["notes"] = notes

    if contact_name:
        contact_id = _resolve_name_to_id(contact_name, "contact")
        if not contact_id:
            return f"Could not find a contact matching '{contact_name}'."
        data["contact_id"] = contact_id

    if company_name:
        company_id = _resolve_name_to_id(company_name, "company")
        if not company_id:
            return f"Could not find a company matching '{company_name}'."
        data["company_id"] = company_id

    if not data:
        return "No fields to update."

    updated = deals_sheet.update(deal_id, data)
    if not updated:
        return f"Failed to update deal '{deal_id}'."

    return f"Updated deal **{updated.get('title', deal.get('title', 'Untitled'))}** (ID: {deal_id})."
