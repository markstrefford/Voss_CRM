"""Interaction tools — calls VOSS API over HTTP."""

from mcp_server.api_client import api_get, api_post


def log_interaction(
    contact_id: str,
    type: str,
    subject: str,
    body: str = "",
    direction: str = "",
    deal_id: str = "",
) -> str:
    data = {
        "contact_id": contact_id,
        "type": type,
        "subject": subject,
    }
    if body:
        data["body"] = body
    if direction:
        data["direction"] = direction
    if deal_id:
        data["deal_id"] = deal_id

    result = api_post("/api/interactions", data)
    interaction = result.get("interaction", result)
    msg = f"Logged {type} interaction: **{subject}** (ID: {interaction['id']})"
    suggestion = result.get("suggestion")
    if suggestion:
        msg += f"\n\n💡 Suggestion: {suggestion}"
    return msg


def get_interaction_history(
    contact_id: str = "",
    deal_id: str = "",
    limit: int = 20,
) -> str:
    params = {}
    if contact_id:
        params["contact_id"] = contact_id
    if deal_id:
        params["deal_id"] = deal_id
    if limit != 20:
        params["limit"] = str(limit)

    interactions = api_get("/api/interactions", params)
    if not interactions:
        return "No interactions found."

    lines = [f"Last {len(interactions)} interaction(s):\n"]
    for i in interactions:
        date = (i.get("occurred_at") or i.get("created_at", ""))[:10]
        direction = f" [{i.get('direction')}]" if i.get("direction") else ""
        itype = i.get("type", "note").upper()
        contact = i.get("contact_name", "")
        line = f"- {date} {itype}{direction}: {i.get('subject', '(no subject)')}"
        if contact:
            line += f" — {contact}"
        lines.append(line)
    return "\n".join(lines)
