"""Deal tools — calls VOSS API over HTTP."""

from mcp_server.api_client import api_get, api_post, api_put
from mcp_server.helpers import format_currency


def get_pipeline() -> str:
    deals = api_get("/api/deals")
    if not deals:
        return "No deals in the pipeline."

    stages = {}
    for d in deals:
        stage = d.get("stage", "unknown")
        stages.setdefault(stage, []).append(d)

    stage_order = ["lead", "prospect", "qualified", "proposal", "negotiation", "won", "lost"]
    lines = ["# Deal Pipeline\n"]
    for stage in stage_order:
        if stage not in stages:
            continue
        stage_deals = stages[stage]
        total = sum(float(d.get("value", 0) or 0) for d in stage_deals)
        lines.append(f"## {stage.upper()} ({len(stage_deals)} deals — {format_currency(str(total))})")
        for d in stage_deals:
            val = format_currency(d.get("value", "0"), d.get("currency", "GBP"))
            contact = d.get("contact_name", "")
            lines.append(f"- {d.get('title', 'Untitled')} — {val}" + (f" ({contact})" if contact else "") + f" [ID: {d['id']}]")
        lines.append("")
    return "\n".join(lines)


def get_deal(deal_id: str) -> str:
    deal = api_get(f"/api/deals/{deal_id}")
    lines = [f"# {deal.get('title', 'Untitled')}"]
    lines.append(f"Stage: {deal.get('stage', '').upper()}")
    lines.append(f"Value: {format_currency(deal.get('value', '0'), deal.get('currency', 'GBP'))}")
    if deal.get("contact_name"):
        lines.append(f"Contact: {deal['contact_name']}")
    if deal.get("company_name"):
        lines.append(f"Company: {deal['company_name']}")
    if deal.get("priority"):
        lines.append(f"Priority: {deal['priority']}")
    if deal.get("expected_close"):
        lines.append(f"Expected close: {deal['expected_close']}")
    if deal.get("notes"):
        lines.append(f"Notes: {deal['notes']}")
    lines.append(f"\n_Deal ID: {deal_id} | Created: {deal.get('created_at', 'N/A')[:10]}_")
    return "\n".join(lines)


def update_deal_stage(deal_id: str, stage: str) -> str:
    deal = api_put(f"/api/deals/{deal_id}", {"stage": stage})
    return f"Deal **{deal.get('title', deal_id)}** moved to **{stage.upper()}**."


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
    data = {
        "title": title,
        "stage": stage,
        "currency": currency,
        "priority": priority,
    }
    if contact_name:
        data["contact_name"] = contact_name
    if company_name:
        data["company_name"] = company_name
    if value:
        data["value"] = value
    if expected_close:
        data["expected_close"] = expected_close
    if notes:
        data["notes"] = notes

    deal = api_post("/api/deals", data)
    return f"Created deal **{title}** (ID: {deal['id']}) in stage {stage.upper()}."


def promote_contact_to_deal(
    contact_name_str: str,
    title: str,
    stage: str = "lead",
    value: str = "",
    currency: str = "GBP",
    priority: str = "medium",
    notes: str = "",
) -> str:
    return create_deal(
        title=title,
        contact_name=contact_name_str,
        stage=stage,
        value=value,
        currency=currency,
        priority=priority,
        notes=notes,
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
    data = {}
    for k, v in [
        ("title", title), ("contact_name", contact_name),
        ("company_name", company_name), ("stage", stage),
        ("value", value), ("currency", currency),
        ("priority", priority), ("expected_close", expected_close),
        ("notes", notes),
    ]:
        if v:
            data[k] = v

    if not data:
        return "No fields to update."

    deal = api_put(f"/api/deals/{deal_id}", data)
    return f"Updated deal **{deal.get('title', deal_id)}** (ID: {deal_id})."
