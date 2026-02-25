from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.sheet_service import deals_sheet, follow_ups_sheet, interactions_sheet

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(_user: dict = Depends(get_current_user)):
    deals = deals_sheet.get_all()
    follow_ups = follow_ups_sheet.get_all()
    interactions = interactions_sheet.get_all()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pipeline by stage
    stages = ["lead", "prospect", "qualified", "proposal", "negotiation", "won", "lost"]
    pipeline = {}
    for stage in stages:
        stage_deals = [d for d in deals if d.get("stage") == stage]
        total_value = sum(float(d.get("value") or 0) for d in stage_deals)
        pipeline[stage] = {"count": len(stage_deals), "value": total_value}

    # Overdue follow-ups
    overdue = [
        f for f in follow_ups
        if f.get("status") == "pending" and f.get("due_date", "") < today
    ]

    # Today's follow-ups
    todays = [
        f for f in follow_ups
        if f.get("status") == "pending" and f.get("due_date", "") == today
    ]

    # Recent activity (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_interactions = [
        i for i in interactions
        if i.get("created_at", "") >= week_ago
    ]

    return {
        "pipeline": pipeline,
        "overdue_count": len(overdue),
        "overdue_follow_ups": overdue[:10],
        "todays_follow_ups": todays,
        "recent_activity_count": len(recent_interactions),
        "total_deals": len(deals),
        "total_deal_value": sum(float(d.get("value") or 0) for d in deals if d.get("stage") not in ("won", "lost")),
    }


@router.get("/stale-deals")
async def stale_deals(_user: dict = Depends(get_current_user)):
    deals = deals_sheet.get_all()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()

    stale = [
        d for d in deals
        if d.get("stage") not in ("won", "lost")
        and d.get("updated_at", "") < cutoff
        and d.get("updated_at", "") != ""
    ]

    return {"stale_deals": stale, "count": len(stale)}
