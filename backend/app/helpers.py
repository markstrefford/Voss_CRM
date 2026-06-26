"""Shared helper functions for the Voss CRM backend."""

import json
from datetime import datetime, timezone


def contact_display_name(contact: dict | None, fallback: str = "Unknown") -> str:
    """Return 'First Last' for a contact dict, with consistent fallback.

    Accepts a full contact dict (from sheet_service) or None.
    """
    if not contact:
        return fallback
    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    name = f"{first} {last}".strip()
    return name or fallback


def parse_platform_handles(raw: str) -> dict:
    """Parse JSON platform_handles string, return empty dict on failure."""
    if not raw:
        return {}
    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def find_contact_by_handle(contacts_sheet, platform: str, handle: str) -> dict | None:
    """Search all contacts for a matching platform handle."""
    handle_lower = handle.lower().rstrip("/")
    for contact in contacts_sheet.get_all():
        handles = parse_platform_handles(contact.get("platform_handles", ""))
        stored = handles.get(platform, "").lower().rstrip("/")
        if stored and stored == handle_lower:
            return contact
    return None


# Engagement stages ordered weakest → strongest, so a re-add can only advance
# the stage on an existing contact, never regress an "accepted" back to "new".
ENGAGEMENT_RANK = {
    "": 0, "new": 1, "contacted": 2, "accepted": 3, "replied": 4, "meeting": 5,
}


def _last_name_root(last_name: str) -> str:
    """Normalise a last name for matching: lowercased, trailing credentials/
    suffixes dropped (', CFA', ' (Ph.D)', ' | ...'). 'Mulroy, CFA' -> 'mulroy'."""
    import re

    return re.split(r"[ ,(|]", (last_name or "").strip().lower())[0]


def find_duplicate_contact(
    contacts_sheet, *, linkedin_url="", email="", first_name="", last_name=""
) -> dict | None:
    """Find an existing active contact that is the same person as the one being
    created. Matches in priority order: linkedin_url, then email, then
    normalised first+last name. Archived rows are ignored. Returns None when no
    match — i.e. a genuinely new contact."""
    def _active(rec):
        return rec if rec and rec.get("status") != "archived" else None

    if linkedin_url:
        m = _active(contacts_sheet.find_by_field("linkedin_url", linkedin_url))
        if m:
            return m
    if email:
        m = _active(contacts_sheet.find_by_field("email", email))
        if m:
            return m
    if first_name and last_name:
        fn = first_name.strip().lower()
        ln = _last_name_root(last_name)
        for c in contacts_sheet.get_all():
            if c.get("status") == "archived":
                continue
            if c.get("first_name", "").strip().lower() == fn and \
                    _last_name_root(c.get("last_name", "")) == ln:
                return c
    return None


def build_contact_enrichment(existing: dict, incoming: dict) -> dict:
    """Compute the update to apply when a create matches an existing contact:
    backfill blank fields, advance (never regress) engagement_stage, and leave
    already-set curated fields untouched. Returns {} when nothing changes."""
    updates: dict = {}
    for key, value in incoming.items():
        if not value or key in ("id", "created_at", "company_name"):
            continue
        if key == "engagement_stage":
            if ENGAGEMENT_RANK.get(value, 0) > ENGAGEMENT_RANK.get(
                existing.get("engagement_stage", ""), 0
            ):
                updates[key] = value
        elif not (existing.get(key) or "").strip():
            updates[key] = value
    return updates


def resolve_or_create_company(companies_sheet, name: str) -> str:
    """Resolve a company name to an existing company id, or create a new
    company row with that name and return its id. Empty/whitespace-only
    names return ""; callers treat that as 'no resolution requested'."""
    if not name or not name.strip():
        return ""
    existing = companies_sheet.find_by_field("name", name)
    if existing:
        return existing["id"]
    return companies_sheet.create({"name": name})["id"]


def today_str() -> str:
    """Return today's date as a YYYY-MM-DD string (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def group_follow_ups(
    follow_ups: list[dict], today: str | None = None
) -> dict[str, list[dict]]:
    """Group follow-ups into overdue / today / upcoming / completed buckets.

    Args:
        follow_ups: List of follow-up dicts (must have 'status' and 'due_date').
        today: Optional date string (YYYY-MM-DD). Defaults to today_str().

    Returns:
        {"overdue": [...], "today": [...], "upcoming": [...], "completed": [...]}
    """
    if today is None:
        today = today_str()

    overdue: list[dict] = []
    todays: list[dict] = []
    upcoming: list[dict] = []
    completed: list[dict] = []

    for f in follow_ups:
        if f.get("status") == "completed":
            completed.append(f)
        elif f.get("status") == "pending":
            due = f.get("due_date", "")
            if due < today:
                overdue.append(f)
            elif due == today:
                todays.append(f)
            else:
                upcoming.append(f)

    return {
        "overdue": overdue,
        "today": todays,
        "upcoming": upcoming,
        "completed": completed,
    }
