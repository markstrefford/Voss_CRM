from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.services.search_service import unified_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query("", description="Free-text query, tokens AND-matched across all entities"),
    _user: dict = Depends(get_current_user),
):
    return unified_search(q)
