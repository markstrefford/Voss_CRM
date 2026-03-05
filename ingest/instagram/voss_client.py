"""HTTP client for VOSS API social capture endpoint."""

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def capture_engagement(event: dict) -> dict | None:
    """Send a normalized engagement event to VOSS POST /api/social/capture."""
    if not settings.voss_api_url or not settings.voss_api_key:
        logger.error("VOSS_API_URL or VOSS_API_KEY not configured")
        return None

    client = _get_client()
    url = f"{settings.voss_api_url.rstrip('/')}/api/social/capture"
    headers = {"X-API-Key": settings.voss_api_key}

    try:
        resp = await client.post(url, json=event, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        logger.error(f"VOSS API error: {e}")
        return None
