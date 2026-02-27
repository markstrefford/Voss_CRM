from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models import FollowUp, FollowUpCreate, FollowUpSnooze
from app.services.sheet_service import follow_ups_sheet

router = APIRouter(prefix="/api/follow-ups", tags=["follow-ups"])


@router.get("", response_model=list[FollowUp])
async def list_follow_ups(
    status_filter: str | None = Query(None, alias="status"),
    contact_id: str | None = Query(None),
    overdue: bool | None = Query(None),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if contact_id:
        filters["contact_id"] = contact_id
    records = follow_ups_sheet.get_all(filters or None)

    if overdue:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        records = [
            r for r in records
            if r.get("status") == "pending" and r.get("due_date", "") < today
        ]

    return records


@router.post("", response_model=FollowUp, status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    body: FollowUpCreate,
    _user: dict = Depends(get_current_user),
):
    return follow_ups_sheet.create(body.model_dump())


@router.patch("/{follow_up_id}/complete", response_model=FollowUp)
async def complete_follow_up(
    follow_up_id: str,
    _user: dict = Depends(get_current_user),
):
    record = follow_ups_sheet.update(follow_up_id, {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    return record


@router.patch("/{follow_up_id}/snooze", response_model=FollowUp)
async def snooze_follow_up(
    follow_up_id: str,
    body: FollowUpSnooze,
    _user: dict = Depends(get_current_user),
):
    record = follow_ups_sheet.update(follow_up_id, {
        "due_date": body.due_date,
        "due_time": body.due_time,
        "status": "snoozed",
        "reminder_sent": "FALSE",
    })
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    return record
