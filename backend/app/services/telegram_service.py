import logging
import re
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.config import settings
from app.helpers import contact_display_name, group_follow_ups, today_str
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
        _app.add_handler(CommandHandler("start", cmd_start))
        _app.add_handler(CommandHandler("help", cmd_help))
        _app.add_handler(CommandHandler("today", cmd_today))
        _app.add_handler(CommandHandler("note", cmd_note))
        _app.add_handler(CommandHandler("new", cmd_new))
        _app.add_handler(CommandHandler("find", cmd_find))
        _app.add_handler(CommandHandler("followup", cmd_followup))
        _app.add_handler(CommandHandler("done", cmd_done))
        _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_done_pick))
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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "unknown"
    await update.message.reply_text(
        f"Welcome to Voss CRM!\n\n"
        f"Your chat ID: `{chat_id}`\n\n"
        f"Commands:\n"
        f"/today — today's follow-ups\n"
        f"/done Name — complete a follow-up\n"
        f"/find <query> — search contacts & companies\n"
        f"/note Name — note text\n"
        f"/followup Name — title, 2026-03-01\n"
        f"/new Name, Company, Role\n"
        f"/pipeline — deal summary",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Voss CRM Commands*\n\n"
        "/today — today's follow-ups & overdue\n"
        "/done Name — complete a follow-up\n"
        "/followup Name — title, date — schedule follow-up\n"
        "/note Name — note text — log an interaction\n"
        "/new Name, Company, Role — create contact\n"
        "/find query — search contacts & companies\n"
        "/pipeline — deal summary\n"
        "/help — show this message",
        parse_mode="Markdown",
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = today_str()
    follow_ups = follow_ups_sheet.get_all({"status": "pending"})
    groups = group_follow_ups(follow_ups, today)
    overdue = groups["overdue"]
    todays = groups["today"]

    lines = ["*Today's Follow-ups*\n"]

    if overdue:
        lines.append(f"*Overdue ({len(overdue)}):*")
        for f in overdue[:10]:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = contact_display_name(contact)
            lines.append(f"  ❗ {f.get('title', '')} — {name} (due {f.get('due_date', '')})")

    if todays:
        lines.append(f"\n*Due Today ({len(todays)}):*")
        for f in todays:
            contact = contacts_sheet.get_by_id(f.get("contact_id", ""))
            name = contact_display_name(contact)
            time_str = f" at {f['due_time']}" if f.get("due_time") else ""
            lines.append(f"  • {f.get('title', '')} — {name}{time_str}")

    if not overdue and not todays:
        lines.append("No follow-ups for today! ✅")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text or "—" not in text and " - " not in text:
        await update.message.reply_text(
            "Usage: /note John Smith — great call, wants proposal\n"
            "Or: /note John Smith - great call, wants proposal"
        )
        return

    # Split on em-dash or regular dash
    sep = "—" if "—" in text else " - "
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

    name = contact_display_name(contact)
    await update.message.reply_text(f"✅ Note added for *{name}*:\n_{note_body}_", parse_mode="Markdown")


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: /new Jane Doe, Acme Corp, CTO, consulting, nurturing, linkedin\n"
            "Fields: name, company, role, segment, stage, channel\n"
            "Only name is required — the rest are optional."
        )
        return

    parts = [p.strip() for p in text.split(",")]
    name_parts = parts[0].split() if parts else []

    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    company_name = parts[1] if len(parts) > 1 else ""
    role = parts[2] if len(parts) > 2 else ""
    segment = parts[3] if len(parts) > 3 else ""
    engagement_stage = parts[4] if len(parts) > 4 else "new"
    inbound_channel = parts[5] if len(parts) > 5 else ""

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
        "segment": segment,
        "engagement_stage": engagement_stage,
        "inbound_channel": inbound_channel,
    })

    name = contact_display_name(contact)
    company_str = f" at {company_name}" if company_name else ""
    role_str = f" ({role})" if role else ""
    extras = []
    if segment:
        extras.append(segment)
    if engagement_stage and engagement_stage != "new":
        extras.append(engagement_stage)
    if inbound_channel:
        extras.append(inbound_channel)
    extras_str = f"\n{' · '.join(extras)}" if extras else ""
    await update.message.reply_text(
        f"✅ Created contact: *{name}*{role_str}{company_str}{extras_str}\nID: `{contact['id']}`",
        parse_mode="Markdown",
    )


async def cmd_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text or "—" not in text and " - " not in text:
        await update.message.reply_text(
            "Usage: /followup John Smith — Send proposal, 2026-03-01\n"
            "Or: /followup John Smith - Send proposal, 2026-03-01\n\n"
            "Format: Name — title, due_date, due_time (optional)\n"
            "Example: /followup David Clark — Call re: contract, 2026-03-05, 14:00"
        )
        return

    # Split name from the rest on em-dash or regular dash
    sep = "—" if "—" in text else " - "
    parts = text.split(sep, 1)
    contact_name = parts[0].strip()
    details = parts[1].strip() if len(parts) > 1 else ""

    if not details:
        await update.message.reply_text("Please provide a title and due date after the dash.")
        return

    # Parse details: title, due_date, due_time (optional)
    detail_parts = [p.strip() for p in details.split(",")]
    title = detail_parts[0] if detail_parts else ""
    due_date = detail_parts[1] if len(detail_parts) > 1 else ""
    due_time = detail_parts[2] if len(detail_parts) > 2 else ""

    if not title or not due_date:
        await update.message.reply_text("Both title and due date are required.\nExample: /followup John Smith — Send proposal, 2026-03-01")
        return

    # Validate date format
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(f"Invalid date format: {due_date}\nUse YYYY-MM-DD (e.g. 2026-03-01)")
        return

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
    follow_ups_sheet.create({
        "contact_id": contact["id"],
        "title": title,
        "due_date": due_date,
        "due_time": due_time,
        "status": "pending",
    })

    name = contact_display_name(contact)
    time_str = f" at {due_time}" if due_time else ""
    await update.message.reply_text(
        f"✅ Follow-up scheduled for *{name}*:\n_{title}_\nDue: {due_date}{time_str}",
        parse_mode="Markdown",
    )


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /done John Smith")
        return

    # Search for contact
    name_parts = text.strip().split()
    contacts = contacts_sheet.search(name_parts[0], ["first_name", "last_name"])
    if len(name_parts) > 1:
        contacts = [
            c for c in contacts
            if name_parts[-1].lower() in c.get("last_name", "").lower()
        ]

    if not contacts:
        await update.message.reply_text(f"Contact '{text}' not found.")
        return

    contact = contacts[0]
    name = contact_display_name(contact)

    # Get pending follow-ups for this contact
    pending = [
        f for f in follow_ups_sheet.get_all({"status": "pending"})
        if f.get("contact_id") == contact["id"]
    ]

    if not pending:
        await update.message.reply_text(f"No pending follow-ups for *{name}*.", parse_mode="Markdown")
        return

    if len(pending) == 1:
        # Only one — complete it directly
        fup = pending[0]
        follow_ups_sheet.update(fup["id"], {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        await update.message.reply_text(
            f"✅ Completed: *{fup.get('title', '')}* — {name}",
            parse_mode="Markdown",
        )
        return

    # Multiple — list them for the user to pick
    pending.sort(key=lambda f: f.get("due_date", ""))
    lines = [f"*{name}* has {len(pending)} pending follow-ups:\n"]
    for i, fup in enumerate(pending, 1):
        due = fup.get("due_date", "no date")
        lines.append(f"  {i}. {fup.get('title', '')} (due {due})")
    lines.append(f"\nReply with the number (1-{len(pending)}) to complete it.")

    # Store the choices so handle_done_pick can resolve the reply
    context.user_data["done_choices"] = pending
    context.user_data["done_contact_name"] = name

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_done_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a numeric reply to a /done multi-choice prompt."""
    choices = context.user_data.get("done_choices")
    if not choices:
        return  # Not in a /done flow — ignore

    text = update.message.text.strip()
    if not text.isdigit():
        # Clear state so we don't keep intercepting messages
        context.user_data.pop("done_choices", None)
        context.user_data.pop("done_contact_name", None)
        return

    pick = int(text)
    name = context.user_data.get("done_contact_name", "")

    # Clear state regardless of outcome
    context.user_data.pop("done_choices", None)
    context.user_data.pop("done_contact_name", None)

    if pick < 1 or pick > len(choices):
        await update.message.reply_text(f"Pick a number between 1 and {len(choices)}.")
        return

    fup = choices[pick - 1]
    follow_ups_sheet.update(fup["id"], {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    await update.message.reply_text(
        f"✅ Completed: *{fup.get('title', '')}* — {name}",
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
            name = contact_display_name(c)
            meta = " · ".join(filter(None, [c.get("segment"), c.get("engagement_stage")]))
            meta_str = f" [{meta}]" if meta else ""
            lines.append(f"  • {name} — {c.get('role', '')} | {c.get('email', '')}{meta_str}")

    if companies:
        lines.append(f"\n*Companies ({len(companies)}):*")
        for co in companies[:5]:
            lines.append(f"  • {co.get('name', '')} — {co.get('industry', '')}")

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
