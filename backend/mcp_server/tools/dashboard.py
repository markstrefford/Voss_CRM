"""Dashboard tools for the MCP server."""

from datetime import datetime, timedelta, timezone

from app.services.sheet_service import deals_sheet, follow_ups_sheet, interactions_sheet
from mcp_server.helpers import resolve_contact_name, format_currency


def get_dashboard_summary() -> str:
    """Get a high-level CRM dashboard: pipeline summary, overdue follow-ups, today's tasks, and recent activity."""
    deals = deals_sheet.get_all()
    follow_ups = follow_ups_sheet.get_all()
    interactions = interactions_sheet.get_all()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Pipeline
    stages = ["lead", "prospect", "qualified", "proposal", "negotiation", "won", "lost"]
    total_active_value = 0.0
    total_active_count = 0
    pipeline_lines = []
    for stage in stages:
        stage_deals = [d for d in deals if d.get("stage") == stage]
        stage_value = sum(float(d.get("value") or 0) for d in stage_deals)
        if stage not in ("won", "lost"):
            total_active_value += stage_value
            total_active_count += len(stage_deals)
        if stage_deals:
            pipeline_lines.append(
                f"  {stage.upper()}: {len(stage_deals)} deal(s), {format_currency(str(stage_value))}"
            )

    # Overdue
    overdue = [
        f for f in follow_ups
        if f.get("status") == "pending" and f.get("due_date", "") < today
    ]

    # Today
    todays = [
        f for f in follow_ups
        if f.get("status") == "pending" and f.get("due_date", "") == today
    ]

    # Recent activity
    recent = [i for i in interactions if i.get("created_at", "") >= week_ago]

    # Build output
    lines = ["# CRM Dashboard\n"]

    lines.append(f"## Pipeline ({total_active_count} active, {format_currency(str(total_active_value))})")
    lines.extend(pipeline_lines)
    lines.append("")

    if overdue:
        lines.append(f"## Overdue Follow-ups ({len(overdue)})")
        for f in sorted(overdue, key=lambda x: x.get("due_date", ""))[:10]:
            name = resolve_contact_name(f.get("contact_id", ""))
            lines.append(f"  - {f.get('title', 'Untitled')} — {name} (due {f.get('due_date', '?')})")
        if len(overdue) > 10:
            lines.append(f"  ... and {len(overdue) - 10} more")
        lines.append("")

    if todays:
        lines.append(f"## Today's Follow-ups ({len(todays)})")
        for f in todays:
            name = resolve_contact_name(f.get("contact_id", ""))
            time = f" at {f['due_time']}" if f.get("due_time") else ""
            lines.append(f"  - {f.get('title', 'Untitled')} — {name}{time}")
        lines.append("")

    lines.append("## Activity")
    lines.append(f"  - {len(recent)} interaction(s) in the last 7 days")
    lines.append(f"  - {len(deals)} total deals")
    lines.append(f"  - Active pipeline value: {format_currency(str(total_active_value))}")

    return "\n".join(lines)
