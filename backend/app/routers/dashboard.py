from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.helpers import contact_display_name, today_str
from app.services.sheet_service import (
    contacts_sheet,
    companies_sheet,
    deals_sheet,
    follow_ups_sheet,
    interactions_sheet,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(_user: dict = Depends(get_current_user)):
    deals = deals_sheet.get_all()
    follow_ups = follow_ups_sheet.get_all()
    interactions = interactions_sheet.get_all()
    today = today_str()

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


def _days_ago_label(date_str: str, now: datetime) -> str:
    """Return a human-readable '2d ago' / 'today' label from an ISO date string."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        delta = (now - dt).days
    except (ValueError, TypeError):
        # Fallback: try date-only format
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            delta = (now - dt).days
        except (ValueError, TypeError):
            return ""
    if delta <= 0:
        return "today"
    if delta == 1:
        return "1d ago"
    return f"{delta}d ago"


@router.get("/action-feed")
async def action_feed(_user: dict = Depends(get_current_user)):
    """Smart queues: surfaces who needs attention right now and why."""
    now = datetime.now(timezone.utc)
    today = today_str()
    week_ago = (now - timedelta(days=7)).isoformat()
    two_weeks_ago = (now - timedelta(days=14)).isoformat()
    end_of_week = (now + timedelta(days=(6 - now.weekday()))).strftime("%Y-%m-%d")

    # Load all sheets (cached 30s by SheetService)
    contacts = contacts_sheet.get_all()
    companies = companies_sheet.get_all()
    deals = deals_sheet.get_all()
    follow_ups = follow_ups_sheet.get_all()
    interactions = interactions_sheet.get_all()

    # Build lookup maps
    contact_map = {c["id"]: c for c in contacts}
    company_map = {c["id"]: c for c in companies}

    def company_name_for(contact: dict) -> str:
        cid = contact.get("company_id", "")
        return company_map.get(cid, {}).get("name", "")

    # --- Stats ---
    active_contacts = [c for c in contacts if c.get("status", "") != "archived"]
    in_conversation = [c for c in contacts if c.get("engagement_stage") in ("active", "engaged")]
    pending_follow_ups = [f for f in follow_ups if f.get("status") == "pending"]
    follow_ups_this_week = [
        f for f in pending_follow_ups
        if f.get("due_date", "") <= end_of_week
    ]
    active_deals = [d for d in deals if d.get("stage") not in ("won", "lost")]
    pipeline_value = sum(float(d.get("value") or 0) for d in active_deals)

    stats = {
        "total_active_contacts": len(active_contacts),
        "in_conversation": len(in_conversation),
        "follow_ups_this_week": len(follow_ups_this_week),
        "deals_in_pipeline": len(active_deals),
        "pipeline_value": pipeline_value,
    }

    # --- Action Required: overdue + due today ---
    def follow_up_item(f: dict) -> dict:
        c = contact_map.get(f.get("contact_id", ""), {})
        return {
            "id": f.get("id", ""),
            "contact_id": f.get("contact_id", ""),
            "contact_name": contact_display_name(c),
            "company_name": company_name_for(c),
            "title": f.get("title", ""),
            "due_date": f.get("due_date", ""),
            "due_time": f.get("due_time", ""),
        }

    overdue = [f for f in pending_follow_ups if f.get("due_date", "") and f["due_date"] < today]
    overdue.sort(key=lambda f: f.get("due_date", ""))
    due_today = [f for f in pending_follow_ups if f.get("due_date", "") == today]
    due_today.sort(key=lambda f: f.get("due_time", "") or "99:99")

    action_required = {
        "overdue_follow_ups": [follow_up_item(f) for f in overdue[:15]],
        "due_today": [follow_up_item(f) for f in due_today[:15]],
        "overdue_total": len(overdue),
        "due_today_total": len(due_today),
    }

    # --- Momentum: inbound recent + engaged-no-follow-up ---
    # Build last interaction per contact + recent inbound
    last_interaction_by_contact: dict[str, dict] = {}
    inbound_recent_list: list[dict] = []

    for ix in interactions:
        cid = ix.get("contact_id", "")
        occurred = ix.get("occurred_at", "") or ix.get("created_at", "")
        if not cid or not occurred:
            continue
        existing = last_interaction_by_contact.get(cid)
        if not existing or occurred > existing.get("occurred_at", ""):
            last_interaction_by_contact[cid] = ix

        # Inbound in last 7 days
        if ix.get("direction") == "inbound" and occurred >= week_ago:
            inbound_recent_list.append(ix)

    # Sort inbound by most recent first
    inbound_recent_list.sort(key=lambda ix: ix.get("occurred_at", "") or ix.get("created_at", ""), reverse=True)

    # Deduplicate by contact (keep most recent inbound per contact)
    seen_contacts: set[str] = set()
    inbound_unique: list[dict] = []
    for ix in inbound_recent_list:
        cid = ix.get("contact_id", "")
        if cid not in seen_contacts:
            seen_contacts.add(cid)
            inbound_unique.append(ix)

    def contact_item(c: dict, reason: str) -> dict:
        last_ix = last_interaction_by_contact.get(c.get("id", ""))
        last_date = ""
        if last_ix:
            last_date = (last_ix.get("occurred_at", "") or last_ix.get("created_at", ""))[:10]
        return {
            "id": c.get("id", ""),
            "name": contact_display_name(c),
            "company_name": company_name_for(c),
            "role": c.get("role", ""),
            "engagement_stage": c.get("engagement_stage", ""),
            "last_interaction_date": last_date,
            "reason": reason,
        }

    # Inbound recent contacts
    inbound_contacts: list[dict] = []
    for ix in inbound_unique[:10]:
        c = contact_map.get(ix.get("contact_id", ""))
        if c:
            occurred = ix.get("occurred_at", "") or ix.get("created_at", "")
            label = _days_ago_label(occurred, now)
            ix_type = ix.get("type", "message")
            reason = f"Replied via {ix_type} {label}".strip()
            inbound_contacts.append(contact_item(c, reason))

    # Engaged in last 7d but no pending follow-up
    contacts_with_pending_fu = {f.get("contact_id") for f in pending_follow_ups}
    engaged_no_fu: list[dict] = []
    for cid, ix in last_interaction_by_contact.items():
        occurred = ix.get("occurred_at", "") or ix.get("created_at", "")
        if occurred >= week_ago and cid not in contacts_with_pending_fu:
            c = contact_map.get(cid)
            if c and c.get("engagement_stage") not in ("new", ""):
                label = _days_ago_label(occurred, now)
                engaged_no_fu.append(contact_item(c, f"Active {label}, no follow-up scheduled"))

    engaged_no_fu.sort(key=lambda x: x.get("last_interaction_date", ""), reverse=True)

    momentum = {
        "inbound_recent": inbound_contacts[:10],
        "no_follow_up_scheduled": engaged_no_fu[:10],
        "inbound_recent_total": len(inbound_unique),
        "no_follow_up_scheduled_total": len(engaged_no_fu),
    }

    # --- At Risk: going cold + stale deals ---
    going_cold: list[dict] = []
    for c in contacts:
        if c.get("engagement_stage") not in ("active", "engaged", "nurturing"):
            continue
        cid = c.get("id", "")
        last_ix = last_interaction_by_contact.get(cid)
        if last_ix:
            occurred = last_ix.get("occurred_at", "") or last_ix.get("created_at", "")
            if occurred and occurred < two_weeks_ago:
                label = _days_ago_label(occurred, now)
                going_cold.append(contact_item(c, f"No interaction for {label}"))
        else:
            # Has engagement stage but zero interactions — also at risk
            created = c.get("created_at", "")
            if created and created < two_weeks_ago:
                going_cold.append(contact_item(c, "No interactions recorded"))

    going_cold.sort(key=lambda x: x.get("last_interaction_date", ""))

    stale_deals_list: list[dict] = []
    for d in active_deals:
        updated = d.get("updated_at", "")
        if updated and updated < two_weeks_ago:
            c = contact_map.get(d.get("contact_id", ""), {})
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                days_stale = (now - dt).days
            except (ValueError, TypeError):
                days_stale = 0
            stale_deals_list.append({
                "id": d.get("id", ""),
                "title": d.get("title", ""),
                "contact_name": contact_display_name(c),
                "company_name": company_name_for(c),
                "stage": d.get("stage", ""),
                "value": float(d.get("value") or 0),
                "days_stale": days_stale,
            })

    stale_deals_list.sort(key=lambda x: x.get("days_stale", 0), reverse=True)

    at_risk = {
        "going_cold": going_cold[:10],
        "stale_deals": stale_deals_list[:10],
        "going_cold_total": len(going_cold),
        "stale_deals_total": len(stale_deals_list),
    }

    # --- Ready to Reach Out: new contacts with no interactions ---
    new_contacts: list[dict] = []
    contacts_with_interactions = set(last_interaction_by_contact.keys())
    for c in contacts:
        if c.get("engagement_stage", "new") == "new" and c.get("id") not in contacts_with_interactions:
            if c.get("status", "") != "archived":
                new_contacts.append(contact_item(c, "No outreach yet"))

    new_contacts.sort(key=lambda x: x.get("name", ""))

    ready_to_reach_out = {
        "new_contacts": new_contacts[:20],
        "new_contacts_total": len(new_contacts),
    }

    return {
        "stats": stats,
        "action_required": action_required,
        "momentum": momentum,
        "at_risk": at_risk,
        "ready_to_reach_out": ready_to_reach_out,
    }
