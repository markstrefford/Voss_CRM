"""Deal tools for the MCP server."""

from app.services.sheet_service import deals_sheet, interactions_sheet
from mcp_server.helpers import resolve_contact_name, resolve_company_name, format_currency

VALID_STAGES = ["lead", "prospect", "qualified", "proposal", "negotiation", "won", "lost"]


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
