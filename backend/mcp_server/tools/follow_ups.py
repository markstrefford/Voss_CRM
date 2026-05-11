"""Follow-up tools — calls VOSS API over HTTP."""

from mcp_server.api_client import api_get, api_patch, api_post, api_put


_UPDATE_FIELDS = ("title", "due_date", "due_time", "notes", "status")


def get_follow_ups(
    status: str = "pending",
    overdue_only: bool = False,
    contact_id: str = "",
) -> str:
    params = {"status": status}
    if contact_id:
        params["contact_id"] = contact_id

    fups = api_get("/api/follow-ups", params)
    if not fups:
        return "No follow-ups found."

    if overdue_only:
        from datetime import date
        today = date.today().isoformat()
        fups = [f for f in fups if f.get("due_date", "") < today]
        if not fups:
            return "No overdue follow-ups."

    lines = [f"Found {len(fups)} follow-up(s):\n"]
    for f in fups:
        due = f.get("due_date", "no date")
        if f.get("due_time"):
            due += f" {f['due_time']}"
        contact = f.get("contact_name", "")
        line = f"- {f.get('title', 'Untitled')} — due {due}"
        if contact:
            line += f" ({contact})"
        line += f" [ID: {f['id']}]"
        lines.append(line)
    return "\n".join(lines)


def create_follow_up(
    contact_id: str,
    title: str,
    due_date: str,
    due_time: str = "",
    deal_id: str = "",
    notes: str = "",
) -> str:
    data = {
        "contact_id": contact_id,
        "title": title,
        "due_date": due_date,
    }
    if due_time:
        data["due_time"] = due_time
    if deal_id:
        data["deal_id"] = deal_id
    if notes:
        data["notes"] = notes

    fup = api_post("/api/follow-ups", data)
    return f"Created follow-up **{title}** due {due_date} (ID: {fup['id']})."


def complete_follow_up(follow_up_id: str) -> str:
    fup = api_patch(f"/api/follow-ups/{follow_up_id}/complete")
    return f"Follow-up **{fup.get('title', follow_up_id)}** marked as completed."


def update_follow_up(
    follow_up_id: str,
    title: str = "",
    due_date: str = "",
    due_time: str = "",
    notes: str = "",
    status: str = "",
) -> str:
    """Update an existing follow-up's title, due date/time, notes, or status.
    For rescheduling specifically (which also flips status to 'snoozed'), use
    snooze_follow_up instead."""
    payload = {k: v for k, v in locals().items() if k in _UPDATE_FIELDS and v}
    if not payload:
        return "No fields to update."
    fup = api_put(f"/api/follow-ups/{follow_up_id}", payload)
    title_disp = fup.get("title") or follow_up_id
    return f"Updated follow-up \"{title_disp}\" (ID: {follow_up_id})."


def snooze_follow_up(
    follow_up_id: str,
    due_date: str,
    due_time: str = "",
) -> str:
    """Reschedule a follow-up to a new date/time. Sets status to 'snoozed'
    and clears reminder_sent so the new date triggers a fresh notification.
    due_date is required (YYYY-MM-DD)."""
    if not due_date or not due_date.strip():
        raise ValueError("snooze_follow_up requires a due_date (YYYY-MM-DD)")
    fup = api_patch(
        f"/api/follow-ups/{follow_up_id}/snooze",
        {"due_date": due_date, "due_time": due_time},
    )
    title_disp = fup.get("title") or follow_up_id
    when = due_date + (f" {due_time}" if due_time else "")
    return f"Snoozed follow-up \"{title_disp}\" until {when} (ID: {follow_up_id})."
