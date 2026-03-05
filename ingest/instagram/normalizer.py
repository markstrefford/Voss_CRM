"""Parse Meta webhook payloads into normalized engagement events."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def normalize_webhook_entry(entry: dict) -> list[dict]:
    """Convert a single Meta webhook entry into a list of normalized engagement events.

    Meta sends batched entries; each entry can contain multiple changes.
    """
    events = []

    for change in entry.get("changes", []):
        field = change.get("field", "")
        value = change.get("value", {})

        if field == "comments":
            event = _normalize_comment(value)
            if event:
                events.append(event)

        elif field == "likes":
            event = _normalize_like(value)
            if event:
                events.append(event)

        elif field == "follows":
            event = _normalize_follow(value)
            if event:
                events.append(event)

        else:
            logger.debug(f"Ignoring unsupported field: {field}")

    return events


def _normalize_comment(value: dict) -> dict | None:
    """Normalize an Instagram comment event."""
    username = value.get("from", {}).get("username", "")
    if not username:
        return None

    return {
        "platform": "instagram",
        "person": {
            "handle": f"@{username}",
            "display_name": value.get("from", {}).get("name", username),
            "profile_url": f"https://instagram.com/{username}",
        },
        "action": "comment",
        "content_ref": {
            "post_url": value.get("media", {}).get("permalink", ""),
            "post_title": "",
        },
        "text": value.get("text", ""),
        "timestamp": value.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }


def _normalize_like(value: dict) -> dict | None:
    """Normalize an Instagram like event."""
    username = value.get("from", {}).get("username", "")
    # Likes may not always include username — Meta sends user ID
    if not username:
        user_id = value.get("from", {}).get("id", "")
        username = f"user_{user_id}" if user_id else ""
    if not username:
        return None

    return {
        "platform": "instagram",
        "person": {
            "handle": f"@{username}",
            "display_name": value.get("from", {}).get("name", username),
            "profile_url": f"https://instagram.com/{username}",
        },
        "action": "like",
        "content_ref": {
            "post_url": value.get("media", {}).get("permalink", ""),
            "post_title": "",
        },
        "text": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_follow(value: dict) -> dict | None:
    """Normalize an Instagram follow event."""
    username = value.get("username", "")
    if not username:
        return None

    return {
        "platform": "instagram",
        "person": {
            "handle": f"@{username}",
            "display_name": value.get("name", username),
            "profile_url": f"https://instagram.com/{username}",
        },
        "action": "follow",
        "content_ref": {
            "post_url": "",
            "post_title": "",
        },
        "text": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
