"""Follow-up tools — calls VOSS API over HTTP."""

from mcp_server.api_client import api_get, api_post, api_put


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
    fup = api_put(f"/api/follow-ups/{follow_up_id}", {"status": "completed"})
    return f"Follow-up **{fup.get('title', follow_up_id)}** marked as completed."
