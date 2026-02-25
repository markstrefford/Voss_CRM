import logging
import re
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.services.sheet_service import (
    companies_sheet,
    contacts_sheet,
    deals_sheet,
    follow_ups_sheet,
    interactions_sheet,
)

logger = logging.getLogger(__name__)

_app: Application | None = None


async def get_telegram_app() -> Application | None:
    global _app
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        return None
    if _app is None:
        _app = Application.builder().token(settings.telegram_bot_token).build()
        _app.add_handler(CommandHandler("today", cmd_today))
        _app.add_handler(CommandHandler("note", cmd_note))
        _app.add_handler(CommandHandler("new", cmd_new))
        _app.add_handler(CommandHandler("find", cmd_find))
        _app.add_handler(CommandHandler("pipeline", cmd_pipeline))
        await _app.initialize()
        await _app.start()
        await _app.updater.start_polling()
    return _app


async def stop_telegram_app():
    global _app
    if _app:
        await _app.updater.stop()
        await _app.stop()
        await _app.shutdown()
        _app = None


async def send_message(chat_id: str, text: str):
    app = await get_telegram_app()
    if app:
        await app.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="Markdown")


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    follow_ups = follow_ups_sheet.get_all({"status": "pending"})

    overdue = [f for f in follow_ups if f.get("due_date", "") < today]
    todays = [f for f in follow_ups if f.get("due_date", "") == today]

    lines = ["*Today's Follow-ups*\n"]

    if overdue:
        lines.append(f"*Overdue ({len(overdue)}):*")
        for f in overdue[:10]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = f"{contact['first_name']} {contact['last_name']}" if contact else "Unknown"
            lines.append(f"  \u2757 {f.get('title', '')} — {name} (due {f.get('due_date', '')})")

    if todays:
        lines.append(f"\n*Due Today ({len(todays)}):*")
        for f in todays:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = f"{contact['first_name']} {contact['last_name']}" if contact else "Unknown"
            time_str = f" at {f['due_time']}" if f.get("due_time") else ""
            lines.append(f"  \u2022 {f.get('title', '')} — {name}{time_str}")

    if not overdue and not todays:
        lines.append("No follow-ups for today! \u2705")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text or "\u2014" not in text and " - " not in text:
        await update.message.reply_text(
            "Usage: /note John Smith \u2014 great call, wants proposal\n"
            "Or: /note John Smith - great call, wants proposal"
        )
        return

    # Split on em-dash or regular dash
    sep = "\u2014" if "\u2014" in text else " - "
    parts = text.split(sep, 1)
    contact_name = parts[0].strip()
    note_body = parts[1].strip() if len(parts) > 1 else ""

    # Extract URLs from note body
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, note_body)
    url_str = urls[0] if urls else ""

    # Search for contact
    name_parts = contact_name.split()
    contacts = contacts_sheet.search(name_parts[0], ["first_name", "last_name"])
    if len(name_parts) > 1:
        contacts = [
            c for c in contacts
            if name_parts[-1].lower() in c.get("last_name", "").lower()
        ]

    if not contacts:
        await update.message.reply_text(f"Contact '{contact_name}' not found.")
        return

    contact = contacts[0]
    interactions_sheet.create({
        "contact_id": contact["id"],
        "type": "note",
        "subject": note_body[:50],
        "body": note_body,
        "url": url_str,
        "direction": "internal",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    })

    name = f"{contact['first_name']} {contact['last_name']}"
    await update.message.reply_text(f"\u2705 Note added for *{name}*:\n_{note_body}_", parse_mode="Markdown")


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /new Jane Doe, Acme Corp, CTO")
        return

    parts = [p.strip() for p in text.split(",")]
    name_parts = parts[0].split() if parts else []

    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    company_name = parts[1] if len(parts) > 1 else ""
    role = parts[2] if len(parts) > 2 else ""

    # Resolve company
    company_id = ""
    if company_name:
        company = companies_sheet.find_by_field("name", company_name)
        if company:
            company_id = company["id"]
        else:
            new_company = companies_sheet.create({"name": company_name})
            company_id = new_company["id"]

    contact = contacts_sheet.create({
        "first_name": first_name,
        "last_name": last_name,
        "company_id": company_id,
        "role": role,
        "source": "telegram",
    })

    name = f"{first_name} {last_name}".strip()
    company_str = f" at {company_name}" if company_name else ""
    role_str = f" ({role})" if role else ""
    await update.message.reply_text(
        f"\u2705 Created contact: *{name}*{role_str}{company_str}\nID: `{contact['id']}`",
        parse_mode="Markdown",
    )


async def cmd_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /find Acme")
        return

    contacts = contacts_sheet.search(query, ["first_name", "last_name", "email", "tags"])
    companies = companies_sheet.search(query, ["name", "industry"])

    lines = [f"*Search: {query}*\n"]

    if contacts:
        lines.append(f"*Contacts ({len(contacts)}):*")
        for c in contacts[:5]:
            name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            lines.append(f"  \u2022 {name} — {c.get('role', '')} | {c.get('email', '')}")

    if companies:
        lines.append(f"\n*Companies ({len(companies)}):*")
        for co in companies[:5]:
            lines.append(f"  \u2022 {co.get('name', '')} — {co.get('industry', '')}")

    if not contacts and not companies:
        lines.append("No results found.")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deals = deals_sheet.get_all()
    active = [d for d in deals if d.get("stage") not in ("won", "lost")]

    stages = ["lead", "prospect", "qualified", "proposal", "negotiation"]
    lines = ["*Pipeline Summary*\n"]

    total_value = 0
    for stage in stages:
        stage_deals = [d for d in active if d.get("stage") == stage]
        value = sum(float(d.get("value") or 0) for d in stage_deals)
        total_value += value
        if stage_deals:
            lines.append(f"  *{stage.title()}*: {len(stage_deals)} deals (${value:,.0f})")

    won = [d for d in deals if d.get("stage") == "won"]
    won_value = sum(float(d.get("value") or 0) for d in won)

    lines.append(f"\n*Total active*: {len(active)} deals (${total_value:,.0f})")
    lines.append(f"*Won*: {len(won)} deals (${won_value:,.0f})")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
