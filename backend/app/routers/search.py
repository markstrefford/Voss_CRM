from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.services.search_service import unified_search

router = APIRouter(prefix="/api/search", tags=["search"])


def _split(value: str) -> list[str]:
    """Split a comma-separated filter param into values, dropping blanks."""
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("")
async def search(
    q: str = Query("", description="Free-text query, tokens AND-matched across all entities"),
    role: str = Query("", description="Comma-separated roles; matches any (substring)"),
    segment: str = Query("", description="Comma-separated segments; matches any (exact)"),
    engagement_stage: str = Query("", description="Comma-separated engagement stages; matches any (exact)"),
    tags: str = Query("", description="Comma-separated tags; matches any (substring)"),
    _user: dict = Depends(get_current_user),
):
    return unified_search(
        q,
        roles=_split(role),
        segments=_split(segment),
        engagement_stages=_split(engagement_stage),
        tags=_split(tags),
    )
