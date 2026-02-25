import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.sheet_service import (
    contacts_sheet,
    deals_sheet,
    follow_ups_sheet,
    users_sheet,
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


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
    """08:00 — overdue follow-ups, today's follow-ups, stale deals."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    follow_ups = follow_ups_sheet.get_all({"status": "pending"})

    overdue = [f for f in follow_ups if f.get("due_date", "") < today]
    todays = [f for f in follow_ups if f.get("due_date", "") == today]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    deals = deals_sheet.get_all()
    stale = [
        d for d in deals
        if d.get("stage") not in ("won", "lost")
        and d.get("updated_at", "") < cutoff
        and d.get("updated_at", "") != ""
    ]

    lines = ["\u2600\ufe0f *Morning Digest*\n"]

    if overdue:
        lines.append(f"\u2757 *{len(overdue)} overdue follow-ups*")
        for f in overdue[:5]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = f"{contact['first_name']} {contact['last_name']}" if contact else "?"
            lines.append(f"  \u2022 {f.get('title', '')} — {name}")

    if todays:
        lines.append(f"\n\ud83d\udcc5 *{len(todays)} follow-ups due today*")
        for f in todays[:5]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = f"{contact['first_name']} {contact['last_name']}" if contact else "?"
            lines.append(f"  \u2022 {f.get('title', '')} — {name}")

    if stale:
        lines.append(f"\n\u26a0\ufe0f *{len(stale)} stale deals* (no update in 14+ days)")
        for d in stale[:5]:
            lines.append(f"  \u2022 {d.get('title', '')} ({d.get('stage', '')})")

    if not overdue and not todays and not stale:
        lines.append("\u2705 All clear! No overdue items.")

    await _send_to_all("\n".join(lines))


async def check_follow_up_reminders():
    """Every 30 min — send reminder for follow-ups with matching due_time."""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    follow_ups = follow_ups_sheet.get_all({"status": "pending"})
    due_now = [
        f for f in follow_ups
        if f.get("due_date", "") == today
        and f.get("due_time", "") == current_time
        and f.get("reminder_sent", "") != "TRUE"
    ]

    for f in due_now:
        contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
        name = f"{contact['first_name']} {contact['last_name']}" if contact else "?"
        text = f"\u23f0 *Reminder*: {f.get('title', '')} — {name}\nDue now!"
        await _send_to_all(text)
        follow_ups_sheet.update(f["id"], {"reminder_sent": "TRUE"})


async def stale_deal_alerts():
    """18:00 — deals with no activity in 14+ days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    deals = deals_sheet.get_all()
    stale = [
        d for d in deals
        if d.get("stage") not in ("won", "lost")
        and d.get("updated_at", "") < cutoff
        and d.get("updated_at", "") != ""
    ]

    if stale:
        lines = [f"\u26a0\ufe0f *{len(stale)} stale deals* need attention:\n"]
        for d in stale[:10]:
            lines.append(f"  \u2022 {d.get('title', '')} ({d.get('stage', '')}) — last update: {d.get('updated_at', '')[:10]}")
        await _send_to_all("\n".join(lines))


def start_scheduler():
    scheduler.add_job(morning_digest, "cron", hour=8, minute=0)
    scheduler.add_job(check_follow_up_reminders, "interval", minutes=30)
    scheduler.add_job(stale_deal_alerts, "cron", hour=18, minute=0)
    scheduler.start()
    logger.info("Scheduler started: morning digest (08:00), reminders (every 30m), stale alerts (18:00)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
