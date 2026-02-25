from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models import Interaction, InteractionCreate, InteractionUpdate
from app.services.sheet_service import interactions_sheet

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=list[Interaction])
async def list_interactions(
    contact_id: str | None = Query(None),
    deal_id: str | None = Query(None),
    type: str | None = Query(None),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if contact_id:
        filters["contact_id"] = contact_id
    if deal_id:
        filters["deal_id"] = deal_id
    if type:
        filters["type"] = type
    return interactions_sheet.get_all(filters or None)


@router.post("", response_model=Interaction, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    body: InteractionCreate,
    _user: dict = Depends(get_current_user),
):
    data = body.model_dump()
    if not data.get("occurred_at"):
        from datetime import datetime, timezone
        data["occurred_at"] = datetime.now(timezone.utc).isoformat()
    return interactions_sheet.create(data)


@router.put("/{interaction_id}", response_model=Interaction)
async def update_interaction(
    interaction_id: str,
    body: InteractionUpdate,
    _user: dict = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_none=True)
    record = interactions_sheet.update(interaction_id, update_data)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return record
