"""Shared helper functions for the Voss CRM backend."""

from datetime import datetime, timezone


def contact_display_name(contact: dict | None, fallback: str = "Unknown") -> str:
    """Return 'First Last' for a contact dict, with consistent fallback.

    Accepts a full contact dict (from sheet_service) or None.
    """
    if not contact:
        return fallback
    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    name = f"{first} {last}".strip()
    return name or fallback


def today_str() -> str:
    """Return today's date as a YYYY-MM-DD string (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def group_follow_ups(
    follow_ups: list[dict], today: str | None = None
) -> dict[str, list[dict]]:
    """Group follow-ups into overdue / today / upcoming / completed buckets.

    Args:
        follow_ups: List of follow-up dicts (must have 'status' and 'due_date').
        today: Optional date string (YYYY-MM-DD). Defaults to today_str().

    Returns:
        {"overdue": [...], "today": [...], "upcoming": [...], "completed": [...]}
    """
    if today is None:
        today = today_str()

    overdue: list[dict] = []
    todays: list[dict] = []
    upcoming: list[dict] = []
    completed: list[dict] = []

    for f in follow_ups:
        if f.get("status") == "completed":
            completed.append(f)
        elif f.get("status") == "pending":
            due = f.get("due_date", "")
            if due < today:
                overdue.append(f)
            elif due == today:
                todays.append(f)
            else:
                upcoming.append(f)

    return {
        "overdue": overdue,
        "today": todays,
        "upcoming": upcoming,
        "completed": completed,
    }
