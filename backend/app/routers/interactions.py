import asyncio
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models import Interaction, InteractionCreate, InteractionUpdate
from app.services.sheet_service import contacts_sheet, interactions_sheet, notifications_sheet

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

_DEAL_KEYWORDS = re.compile(
    r"\b(cv|resume|résumé|proposal|application|job|applied|submitted|offer|contract|placement|candidate)\b",
    re.IGNORECASE,
)


def check_deal_suggestion(
    subject: str, body: str, interaction_type: str
) -> dict | None:
    """Check if an interaction looks like a deal opportunity.

    Returns {"suggested": True, "title": "<extracted>", "notes": "<context>"} or None.
    Future: swap regex for LLM call without touching callers.
    """
    if interaction_type == "cv_sent":
        title = subject or "CV sent"
        return {"suggested": True, "title": title, "notes": f"From interaction: {subject}"}

    text = f"{subject} {body}"
    match = _DEAL_KEYWORDS.search(text)
    if match:
        title = subject or "New opportunity"
        return {"suggested": True, "title": title, "notes": f"From interaction: {subject}"}

    return None


class DealSuggestion(BaseModel):
    suggested: bool = True
    title: str = ""
    notes: str = ""


class InteractionCreateResponse(BaseModel):
    """Interaction plus optional deal suggestion."""
    id: str
    contact_id: str = ""
    deal_id: str = ""
    type: str = ""
    subject: str = ""
    body: str = ""
    url: str = ""
    direction: str = ""
    occurred_at: str = ""
    created_at: str = ""
    deal_suggestion: DealSuggestion | None = None


@router.get("", response_model=list[Interaction])
async def list_interactions(
    contact_id: str | None = Query(None),
    deal_id: str | None = Query(None),
    type: str | None = Query(None),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if contact_id:
        filters["contact_id"] = contact_id
    if deal_id:
        filters["deal_id"] = deal_id
    if type:
        filters["type"] = type
    return interactions_sheet.get_all(filters or None)


@router.post("", response_model=InteractionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    body: InteractionCreate,
    _user: dict = Depends(get_current_user),
):
    data = body.model_dump()
    if not data.get("occurred_at"):
        from datetime import datetime, timezone
        data["occurred_at"] = datetime.now(timezone.utc).isoformat()
    record = interactions_sheet.create(data)
    suggestion = check_deal_suggestion(
        data.get("subject", ""), data.get("body", ""), data.get("type", "")
    )
    if suggestion:
        asyncio.ensure_future(_notify_deal_suggestion(
            data.get("contact_id", ""), suggestion["title"], suggestion.get("notes", "")
        ))
    return {**record, "deal_suggestion": suggestion}


async def _notify_deal_suggestion(contact_id: str, title: str, notes: str):
    """Create notification record, then send Telegram alert with notification id."""
    try:
        contact = contacts_sheet.get_by_id(contact_id)
        company_id = contact.get("company_id", "") if contact else ""

        notification = notifications_sheet.create({
            "type": "deal_suggestion",
            "status": "pending",
            "contact_id": contact_id,
            "company_id": company_id,
            "title": title,
            "payload": json.dumps({"notes": notes}),
        })

        from app.services.telegram_service import notify_deal_suggestion
        await notify_deal_suggestion(contact_id, title, notes, notification_id=notification["id"])
    except Exception as e:
        logger.error(f"Failed to send deal suggestion notification: {e}")


@router.put("/{interaction_id}", response_model=Interaction)
async def update_interaction(
    interaction_id: str,
    body: InteractionUpdate,
    _user: dict = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_none=True)
    record = interactions_sheet.update(interaction_id, update_data)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return record
