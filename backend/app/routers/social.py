"""Social engagement capture API endpoints.

Used by the Instagram listener and LinkedIn Chrome extension to record
social interactions against VOSS contacts.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.helpers import contact_display_name, find_contact_by_handle, parse_platform_handles
from app.services.sheet_service import contacts_sheet, interactions_sheet

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social"])


# --- Request/Response models ---

class PersonInfo(BaseModel):
    handle: str = ""
    display_name: str = ""
    profile_url: str = ""


class ContentRef(BaseModel):
    post_url: str = ""
    post_title: str = ""


class EngagementEvent(BaseModel):
    platform: str  # "instagram" or "linkedin"
    person: PersonInfo
    action: str  # "comment", "like", "follow", "share", "message", etc.
    content_ref: ContentRef = ContentRef()
    text: str = ""
    timestamp: str = ""


class CaptureResponse(BaseModel):
    contact: dict
    interaction: dict
    match_type: str  # "handle", "name", "new"
    pending_link: bool = False


class BatchLookupRequest(BaseModel):
    items: list[PersonInfo]


class BatchLookupResult(BaseModel):
    handle: str
    display_name: str
    found: bool
    contact_id: str = ""
    contact_name: str = ""


# --- Helpers ---

def _build_interaction_body(event: EngagementEvent) -> str:
    """Build a human-readable interaction body from an engagement event."""
    platform = event.platform.title()
    action = event.action
    person = event.person.display_name or event.person.handle

    post_ref = ""
    if event.content_ref.post_title:
        post_ref = f" on '{event.content_ref.post_title}'"
    elif event.content_ref.post_url:
        post_ref = f" on {event.content_ref.post_url}"

    text_part = ""
    if event.text:
        text_part = f": \"{event.text}\""

    action_map = {
        "comment": f"Commented{post_ref}{text_part}",
        "like": f"Liked{post_ref}",
        "follow": "Started following",
        "share": f"Shared{post_ref}",
        "message": f"Message{text_part}",
        "dm": f"DM{text_part}",
        "story_mention": "Mentioned you in their story",
        "story_reply": f"Replied to your story{text_part}",
        "connection_request": "Sent connection request",
    }

    body = action_map.get(action, f"{action}{post_ref}{text_part}")
    return f"[{platform}] {body}"


def _search_contact_by_name(name: str) -> dict | None:
    """Search contacts by display name, return best match or None."""
    if not name:
        return None
    parts = name.split()
    if not parts:
        return None
    results = contacts_sheet.search(parts[0], ["first_name", "last_name"])
    if len(parts) > 1:
        results = [
            c for c in results
            if parts[-1].lower() in c.get("last_name", "").lower()
        ]
    return results[0] if results else None


# --- Endpoints ---

@router.post("/capture", response_model=CaptureResponse)
async def capture_engagement(
    event: EngagementEvent,
    _user: dict = Depends(get_current_user),
):
    """Capture a social engagement event. Handles contact matching and interaction logging."""
    now = datetime.now(timezone.utc).isoformat()
    timestamp = event.timestamp or now

    # 1. Search by platform handle
    contact = None
    match_type = "new"
    pending_link = False

    if event.person.handle:
        contact = find_contact_by_handle(contacts_sheet, event.platform, event.person.handle)
        if contact:
            match_type = "handle"

    # 2. Fall back to name search
    if not contact and event.person.display_name:
        contact = _search_contact_by_name(event.person.display_name)
        if contact:
            match_type = "name"
            pending_link = True  # Name match but no handle match — needs confirmation

    # 3. Create new contact if no match
    if not contact:
        handles = {}
        if event.person.handle:
            handles[event.platform] = event.person.handle
        name_parts = (event.person.display_name or event.person.handle).split()
        first_name = name_parts[0] if name_parts else event.person.handle
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        contact = contacts_sheet.create({
            "first_name": first_name,
            "last_name": last_name,
            "platform_handles": json.dumps(handles) if handles else "",
            "tags": event.platform,
            "source": f"{event.platform}_organic",
            "engagement_stage": "new",
            "inbound_channel": event.platform,
        })
        match_type = "new"

    # 4. Log interaction
    subject = _build_interaction_body(event)
    interaction = interactions_sheet.create({
        "contact_id": contact["id"],
        "type": "note",
        "subject": subject[:100],
        "body": subject,
        "url": event.content_ref.post_url or event.person.profile_url,
        "direction": "inbound",
        "occurred_at": timestamp,
    })

    # 5. Send Telegram notification for pending links
    if pending_link:
        try:
            from app.services.telegram_service import notify_pending_link
            await notify_pending_link(event, contact)
        except Exception as e:
            logger.warning(f"Failed to send pending_link notification: {e}")

    return CaptureResponse(
        contact=contact,
        interaction=interaction,
        match_type=match_type,
        pending_link=pending_link,
    )


@router.get("/search-handles")
async def search_handles(
    platform: str = Query(...),
    handle: str = Query(...),
    _user: dict = Depends(get_current_user),
):
    """Search contacts by platform handle."""
    contact = find_contact_by_handle(contacts_sheet, platform, handle)
    if contact:
        return {"found": True, "contact": contact}
    return {"found": False, "contact": None}


@router.post("/batch-lookup", response_model=list[BatchLookupResult])
async def batch_lookup(
    body: BatchLookupRequest,
    _user: dict = Depends(get_current_user),
):
    """Check which persons are already in VOSS. Used by Chrome extension to pre-annotate the queue."""
    all_contacts = contacts_sheet.get_all()
    results = []

    for person in body.items:
        found = False
        contact_id = ""
        contact_name = ""

        # Check by handle
        if person.handle:
            handle_lower = person.handle.lower().rstrip("/")
            for c in all_contacts:
                handles = parse_platform_handles(c.get("platform_handles", ""))
                for _platform, stored in handles.items():
                    if stored.lower().rstrip("/") == handle_lower:
                        found = True
                        contact_id = c["id"]
                        contact_name = contact_display_name(c)
                        break
                if found:
                    break

        # Fall back to name search
        if not found and person.display_name:
            parts = person.display_name.split()
            if parts:
                for c in all_contacts:
                    if (parts[0].lower() in c.get("first_name", "").lower()
                            and (len(parts) < 2 or parts[-1].lower() in c.get("last_name", "").lower())):
                        found = True
                        contact_id = c["id"]
                        contact_name = contact_display_name(c)
                        break

        results.append(BatchLookupResult(
            handle=person.handle,
            display_name=person.display_name,
            found=found,
            contact_id=contact_id,
            contact_name=contact_name,
        ))

    return results
