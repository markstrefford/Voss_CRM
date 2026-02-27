"""Follow-up tools for the MCP server."""

from datetime import datetime, timezone

from app.helpers import group_follow_ups, today_str
from app.services.sheet_service import follow_ups_sheet
from mcp_server.helpers import resolve_contact_name


def get_follow_ups(
    status: str = "pending",
    overdue_only: bool = False,
    contact_id: str = "",
) -> str:
    """Get follow-ups, optionally filtered by status, overdue, or contact.

    Args:
        status: Filter by status — 'pending', 'completed', or 'all' (default: pending)
        overdue_only: If true, only return overdue follow-ups
        contact_id: Filter by contact ID
    """
    fups = follow_ups_sheet.get_all()
    today = today_str()

    if status and status != "all":
        fups = [f for f in fups if f.get("status") == status]
    if contact_id:
        fups = [f for f in fups if f.get("contact_id") == contact_id]
    if overdue_only:
        fups = [
            f for f in fups
            if f.get("status") == "pending" and f.get("due_date", "") < today
        ]

    # Sort by due date
    fups.sort(key=lambda f: f.get("due_date", "9999"))

    if not fups:
        label = "overdue follow-ups" if overdue_only else f"{status} follow-ups"
        return f"No {label} found."

    groups = group_follow_ups(fups, today)
    overdue = groups["overdue"]
    todays = groups["today"]
    rest = groups["upcoming"] + groups["completed"]

    lines = ["# Follow-ups\n"]

    if overdue:
        lines.append(f"## Overdue ({len(overdue)})")
        for f in overdue:
            _append_follow_up(lines, f)
        lines.append("")

    if todays:
        lines.append(f"## Today ({len(todays)})")
        for f in todays:
            _append_follow_up(lines, f)
        lines.append("")

    if rest:
        label = "Upcoming" if status == "pending" else "Other"
        lines.append(f"## {label} ({len(rest)})")
        for f in rest:
            _append_follow_up(lines, f)
        lines.append("")

    return "\n".join(lines)


def _append_follow_up(lines: list[str], f: dict) -> None:
    contact = resolve_contact_name(f.get("contact_id", ""))
    due = f.get("due_date", "no date")
    if f.get("due_time"):
        due += f" {f['due_time']}"
    lines.append(f"- **{f.get('title', 'Untitled')}** — {contact}")
    lines.append(f"  Due: {due} | ID: {f['id']}")
    if f.get("notes"):
        lines.append(f"  Notes: {f['notes']}")


def create_follow_up(
    contact_id: str,
    title: str,
    due_date: str,
    due_time: str = "",
    deal_id: str = "",
    notes: str = "",
) -> str:
    """Schedule a new follow-up for a contact.

    Args:
        contact_id: The contact's ID
        title: What to follow up about
        due_date: Due date in YYYY-MM-DD format
        due_time: Optional due time in HH:MM format
        deal_id: Associated deal ID (if applicable)
        notes: Additional notes
    """
    data = {
        "contact_id": contact_id,
        "title": title,
        "due_date": due_date,
        "due_time": due_time,
        "deal_id": deal_id,
        "notes": notes,
        "status": "pending",
    }
    record = follow_ups_sheet.create(data)
    name = resolve_contact_name(contact_id)
    return (
        f"Created follow-up: **{title}** with {name}, due {due_date}"
        + (f" at {due_time}" if due_time else "")
        + f" (ID: {record['id']})"
    )


def complete_follow_up(follow_up_id: str) -> str:
    """Mark a follow-up as completed.

    Args:
        follow_up_id: The follow-up's unique ID
    """
    fup = follow_ups_sheet.get_by_id(follow_up_id)
    if not fup:
        return f"Follow-up '{follow_up_id}' not found."

    if fup.get("status") == "completed":
        return f"Follow-up '{fup.get('title', '')}' is already completed."

    updated = follow_ups_sheet.update(follow_up_id, {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    if not updated:
        return f"Failed to complete follow-up '{follow_up_id}'."

    name = resolve_contact_name(fup.get("contact_id", ""))
    return f"Completed follow-up: **{fup.get('title', '')}** with {name}."
