"""Instagram webhook endpoint handlers."""

import hashlib
import logging

from fastapi import APIRouter, BackgroundTasks, Query, Request, Response

from config import settings
from dedup import is_duplicate
from normalizer import normalize_webhook_entry
from voss_client import capture_engagement

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook/instagram")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification (challenge/response)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning(f"Webhook verification failed: mode={hub_mode}")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook/instagram")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Instagram webhook events from Meta."""
    body = await request.json()
    logger.info(f"Webhook received: object={body.get('object')}")

    if body.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        entry_id = entry.get("id", "")
        for change in entry.get("changes", []):
            # Build a dedup key from entry ID + field + value hash
            field = change.get("field", "")
            value_str = str(change.get("value", {}))
            event_id = hashlib.md5(f"{entry_id}:{field}:{value_str}".encode()).hexdigest()

            if is_duplicate(event_id):
                logger.debug(f"Skipping duplicate event: {event_id}")
                continue

        # Normalize and send to VOSS in the background
        events = normalize_webhook_entry(entry)
        for event in events:
            background_tasks.add_task(_process_event, event)

    # Return 200 immediately per Meta requirements
    return {"status": "ok"}


async def _process_event(event: dict):
    """Process a single engagement event by sending it to VOSS."""
    try:
        result = await capture_engagement(event)
        if result:
            logger.info(
                f"Captured {event['action']} from {event['person']['handle']} "
                f"→ contact={result.get('contact', {}).get('id', '?')}"
            )
        else:
            logger.warning(f"Failed to capture event: {event['person']['handle']}")
    except Exception as e:
        logger.error(f"Error processing event: {e}")
