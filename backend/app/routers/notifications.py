import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.helpers import today_str
from app.models import Notification, NotificationResolve
from app.services.sheet_service import (
    deals_sheet,
    follow_ups_sheet,
    notifications_sheet,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
async def list_notifications(
    status_filter: str | None = Query(None, alias="status"),
    contact_id: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if contact_id:
        filters["contact_id"] = contact_id
    return notifications_sheet.get_all(filters or None, limit=limit, offset=offset)


@router.put("/{notification_id}/resolve", response_model=dict)
async def resolve_notification(
    notification_id: str,
    body: NotificationResolve,
    _user: dict = Depends(get_current_user),
):
    notification = notifications_sheet.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    now = datetime.now(timezone.utc).isoformat()
    updated = notifications_sheet.update(notification_id, {
        "status": body.action,
        "resolved_at": now,
    })

    result = {"notification": updated}

    if body.action == "accepted" and notification.get("type") == "deal_suggestion":
        payload = {}
        try:
            payload = json.loads(notification.get("payload", "{}"))
        except (json.JSONDecodeError, TypeError):
            pass
        deal = deals_sheet.create({
            "title": notification.get("title", ""),
            "contact_id": notification.get("contact_id", ""),
            "company_id": notification.get("company_id", ""),
            "stage": "lead",
            "priority": "medium",
            "notes": payload.get("notes", ""),
        })
        result["deal"] = deal

    elif body.action == "follow_up" and notification.get("type") == "deal_suggestion":
        follow_up = follow_ups_sheet.create({
            "contact_id": notification.get("contact_id", ""),
            "title": f"Review deal: {notification.get('title', '')}",
            "due_date": today_str(),
            "status": "pending",
        })
        result["follow_up"] = follow_up

    return result
