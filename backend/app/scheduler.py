import asyncio
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.helpers import contact_display_name, group_follow_ups, today_str
from app.services.sheet_service import (
    contacts_sheet,
    deals_sheet,
    follow_ups_sheet,
    scheduler_log_sheet,
    users_sheet,
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _already_ran_today(job_name: str) -> bool:
    """Check SchedulerLog sheet — return True if job already ran today."""
    today = today_str()
    row = scheduler_log_sheet.find_by_field("job_name", job_name)
    return row is not None and row.get("last_run_date") == today


def _mark_ran(job_name: str) -> None:
    """Upsert the SchedulerLog row for this job with today's date."""
    today = today_str()
    row = scheduler_log_sheet.find_by_field("job_name", job_name)
    if row:
        scheduler_log_sheet.update(row["id"], {"last_run_date": today})
    else:
        scheduler_log_sheet.create({"job_name": job_name, "last_run_date": today})


def _get_chat_ids() -> list[str]:
    users = users_sheet.get_all()
    return [u["telegram_chat_id"] for u in users if u.get("telegram_chat_id")]


async def _send_to_all(text: str):
    from app.services.telegram_service import send_message
    for chat_id in _get_chat_ids():
        try:
            await send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")


async def morning_digest():
    """09:30 — overdue follow-ups, today's follow-ups, stale deals."""
    if _already_ran_today("morning_digest"):
        logger.info("Morning digest already sent today, skipping")
        return
    _mark_ran("morning_digest")

    today = today_str()
    follow_ups = follow_ups_sheet.get_all({"status": "pending"})
    groups = group_follow_ups(follow_ups, today)
    overdue = groups["overdue"]
    todays = groups["today"]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    deals = deals_sheet.get_all()
    stale = [
        d for d in deals
        if d.get("stage") not in ("won", "lost")
        and d.get("updated_at", "") < cutoff
        and d.get("updated_at", "") != ""
    ]

    lines = ["☀️ *Morning Digest*\n"]

    if overdue:
        lines.append(f"❗ *{len(overdue)} overdue follow-ups*")
        for f in overdue[:5]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = contact_display_name(contact, fallback="?")
            lines.append(f"  • {f.get('title', '')} — {name}")

    if todays:
        lines.append(f"\n📅 *{len(todays)} follow-ups due today*")
        for f in todays[:5]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = contact_display_name(contact, fallback="?")
            lines.append(f"  • {f.get('title', '')} — {name}")

    if stale:
        lines.append(f"\n⚠️ *{len(stale)} stale deals* (no update in 14+ days)")
        for d in stale[:5]:
            lines.append(f"  • {d.get('title', '')} ({d.get('stage', '')})")

    if not overdue and not todays and not stale:
        lines.append("✅ All clear! No overdue items.")

    await _send_to_all("\n".join(lines))


async def check_follow_up_reminders():
    """Every 30 min — send reminder for follow-ups with matching due_time."""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    today = today_str()

    follow_ups = follow_ups_sheet.get_all({"status": "pending"})
    due_now = [
        f for f in follow_ups
        if f.get("due_date", "") == today
        and f.get("due_time", "") == current_time
        and f.get("reminder_sent", "") != "TRUE"
    ]

    for f in due_now:
        contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
        name = contact_display_name(contact, fallback="?")
        text = f"⏰ *Reminder*: {f.get('title', '')} — {name}\nDue now!"
        await _send_to_all(text)
        follow_ups_sheet.update(f["id"], {"reminder_sent": "TRUE"})


async def stale_deal_alerts():
    """18:00 — deals with no activity in 14+ days."""
    if _already_ran_today("stale_deal_alerts"):
        logger.info("Stale deal alerts already sent today, skipping")
        return
    _mark_ran("stale_deal_alerts")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    deals = deals_sheet.get_all()
    stale = [
        d for d in deals
        if d.get("stage") not in ("won", "lost")
        and d.get("updated_at", "") < cutoff
        and d.get("updated_at", "") != ""
    ]

    if stale:
        lines = [f"⚠️ *{len(stale)} stale deals* need attention:\n"]
        for d in stale[:10]:
            lines.append(f"  • {d.get('title', '')} ({d.get('stage', '')}) — last update: {d.get('updated_at', '')[:10]}")
        await _send_to_all("\n".join(lines))


async def _catch_up_missed_jobs():
    """On startup, send any scheduled alerts that were missed today."""
    now = datetime.now(timezone.utc)
    hour_min = now.hour * 60 + now.minute

    # Morning digest at 09:30 — if it's past that, send now
    if hour_min >= 9 * 60 + 30:
        logger.info("Catching up missed morning digest")
        await morning_digest()

    # Stale deal alerts at 18:00 — if it's past that, send now
    if hour_min >= 18 * 60:
        logger.info("Catching up missed stale deal alerts")
        await stale_deal_alerts()


def start_scheduler():
    scheduler.add_job(morning_digest, "cron", hour=9, minute=30, misfire_grace_time=3600)
    scheduler.add_job(check_follow_up_reminders, "interval", minutes=30, misfire_grace_time=600)
    scheduler.add_job(stale_deal_alerts, "cron", hour=18, minute=0, misfire_grace_time=3600)
    scheduler.start()
    logger.info("Scheduler started: morning digest (09:30), reminders (every 30m), stale alerts (18:00)")

    # Catch up any missed jobs from today
    asyncio.ensure_future(_catch_up_missed_jobs())


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
