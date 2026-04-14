"""Dashboard tools — calls VOSS API over HTTP."""

import json

from mcp_server.api_client import api_get


def get_dashboard_summary() -> str:
    summary = api_get("/api/dashboard/summary")
    lines = ["# CRM Dashboard\n"]

    # Pipeline
    pipeline = summary.get("pipeline", {})
    if pipeline:
        lines.append("## Pipeline")
        for stage, data in pipeline.items():
            lines.append(f"- {stage.upper()}: {data.get('count', 0)} deals")
        lines.append("")

    # Follow-ups
    overdue = summary.get("overdue_follow_ups", 0)
    today = summary.get("today_follow_ups", 0)
    if overdue or today:
        lines.append("## Follow-ups")
        if overdue:
            lines.append(f"- 🔴 {overdue} overdue")
        if today:
            lines.append(f"- 📅 {today} due today")
        lines.append("")

    # Stale deals
    stale = summary.get("stale_deals", 0)
    if stale:
        lines.append(f"## Stale Deals\n- ⚠️ {stale} deals with no activity in 14+ days\n")

    return "\n".join(lines)
