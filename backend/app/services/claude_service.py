import anthropic

from app.config import settings
from app.services.sheet_service import contacts_sheet, deals_sheet, interactions_sheet


def draft_email(
    contact_id: str,
    deal_id: str | None = None,
    intent: str = "",
    tone: str = "professional",
) -> dict:
    contact = contacts_sheet.get_by_id(contact_id)
    if not contact:
        raise ValueError("Contact not found")

    # Gather context
    recent_interactions = interactions_sheet.get_all({"contact_id": contact_id})
    recent_interactions.sort(key=lambda x: x.get("occurred_at", ""), reverse=True)
    recent_interactions = recent_interactions[:5]

    deal = None
    if deal_id:
        deal = deals_sheet.get_by_id(deal_id)

    # Build prompt
    context_parts = [
        f"Contact: {contact.get('first_name', '')} {contact.get('last_name', '')}",
        f"Role: {contact.get('role', '')}",
        f"Email: {contact.get('email', '')}",
    ]

    if contact.get("notes"):
        context_parts.append(f"Notes: {contact['notes']}")

    if deal:
        context_parts.append(f"\nDeal: {deal.get('title', '')}")
        context_parts.append(f"Stage: {deal.get('stage', '')}")
        context_parts.append(f"Value: {deal.get('value', '')} {deal.get('currency', '')}")
        if deal.get("notes"):
            context_parts.append(f"Deal notes: {deal['notes']}")

    if recent_interactions:
        context_parts.append("\nRecent interactions:")
        for interaction in recent_interactions:
            context_parts.append(
                f"- [{interaction.get('type', '')}] {interaction.get('occurred_at', '')}: "
                f"{interaction.get('subject', '')} — {interaction.get('body', '')[:200]}"
            )

    context = "\n".join(context_parts)

    prompt = f"""You are drafting an email for a personal CRM user. Based on the context below, draft a {tone} email.

Context:
{context}

Intent: {intent}

Respond with JSON only, no markdown:
{{"subject": "...", "body": "..."}}

The body should be the email text only (no subject line repeated). Use appropriate greeting and sign-off. Keep it concise and natural."""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    try:
        result = json.loads(message.content[0].text)
        return {"subject": result.get("subject", ""), "body": result.get("body", "")}
    except (json.JSONDecodeError, IndexError, KeyError):
        return {"subject": "", "body": message.content[0].text}
