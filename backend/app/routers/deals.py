from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models import Deal, DealCreate, DealStageUpdate, DealUpdate
from app.services.sheet_service import deals_sheet

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("", response_model=list[Deal])
async def list_deals(
    stage: str | None = Query(None),
    priority: str | None = Query(None),
    contact_id: str | None = Query(None),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if stage:
        filters["stage"] = stage
    if priority:
        filters["priority"] = priority
    if contact_id:
        filters["contact_id"] = contact_id
    return deals_sheet.get_all(filters or None)


@router.post("", response_model=Deal, status_code=status.HTTP_201_CREATED)
async def create_deal(
    body: DealCreate,
    _user: dict = Depends(get_current_user),
):
    return deals_sheet.create(body.model_dump())


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(
    deal_id: str,
    _user: dict = Depends(get_current_user),
):
    record = deals_sheet.get_by_id(deal_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return record


@router.put("/{deal_id}", response_model=Deal)
async def update_deal(
    deal_id: str,
    body: DealUpdate,
    _user: dict = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_none=True)
    record = deals_sheet.update(deal_id, update_data)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return record


@router.patch("/{deal_id}/stage", response_model=Deal)
async def update_deal_stage(
    deal_id: str,
    body: DealStageUpdate,
    _user: dict = Depends(get_current_user),
):
    record = deals_sheet.update(deal_id, {"stage": body.stage})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return record
