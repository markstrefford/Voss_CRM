"""Interaction tools for the MCP server."""

from datetime import datetime, timezone

from app.services.sheet_service import interactions_sheet
from mcp_server.helpers import resolve_contact_name


def log_interaction(
    contact_id: str,
    type: str,
    subject: str,
    body: str = "",
    direction: str = "",
    deal_id: str = "",
) -> str:
    """Log an interaction (call, email, meeting, or note) with a contact.

    Args:
        contact_id: The contact's ID
        type: Type of interaction — one of: call, email, meeting, note
        subject: Brief description of the interaction
        body: Full details or notes about the interaction
        direction: For calls/emails — 'inbound' or 'outbound'
        deal_id: Associated deal ID (if applicable)
    """
    data = {
        "contact_id": contact_id,
        "type": type,
        "subject": subject,
        "body": body,
        "direction": direction,
        "deal_id": deal_id,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    record = interactions_sheet.create(data)
    name = resolve_contact_name(contact_id)
    return (
        f"Logged {type} with **{name}**: \"{subject}\" (ID: {record['id']})"
    )


def get_interaction_history(
    contact_id: str = "",
    deal_id: str = "",
    limit: int = 20,
) -> str:
    """Get recent interaction history, optionally filtered by contact or deal.

    Args:
        contact_id: Filter by contact ID
        deal_id: Filter by deal ID
        limit: Maximum number of interactions to return (default 20)
    """
    all_interactions = interactions_sheet.get_all()

    if contact_id:
        all_interactions = [
            i for i in all_interactions if i.get("contact_id") == contact_id
        ]
    if deal_id:
        all_interactions = [
            i for i in all_interactions if i.get("deal_id") == deal_id
        ]

    # Sort by date descending
    all_interactions.sort(
        key=lambda x: x.get("occurred_at", x.get("created_at", "")),
        reverse=True,
    )
    all_interactions = all_interactions[:limit]

    if not all_interactions:
        parts = []
        if contact_id:
            parts.append(f"contact {contact_id}")
        if deal_id:
            parts.append(f"deal {deal_id}")
        scope = " for " + " and ".join(parts) if parts else ""
        return f"No interactions found{scope}."

    scope_name = ""
    if contact_id:
        scope_name = f" with {resolve_contact_name(contact_id)}"

    lines = [f"## Interaction History{scope_name} (showing {len(all_interactions)})\n"]
    for i in all_interactions:
        date = (i.get("occurred_at") or i.get("created_at", ""))[:10]
        itype = i.get("type", "note").upper()
        direction = f" [{i.get('direction')}]" if i.get("direction") else ""
        contact_label = ""
        if not contact_id:
            contact_label = f" — {resolve_contact_name(i.get('contact_id', ''))}"

        lines.append(f"### {date} {itype}{direction}{contact_label}")
        lines.append(f"**{i.get('subject', '(no subject)')}**")
        if i.get("body"):
            body = i["body"][:500]
            if len(i["body"]) > 500:
                body += "..."
            lines.append(body)
        lines.append(f"_ID: {i['id']}_\n")

    return "\n".join(lines)
