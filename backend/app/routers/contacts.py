from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

import json

from app.dependencies import get_current_user
from app.helpers import (
    build_contact_enrichment,
    find_duplicate_contact,
    parse_platform_handles,
    resolve_or_create_company,
)
from app.models import Contact, ContactCreate, ContactFromLinkedIn, ContactUpdate
from app.services.sheet_service import companies_sheet, contacts_sheet

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
async def list_contacts(
    tag: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    company_id: str | None = Query(None),
    segment: str | None = Query(None),
    engagement_stage: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
    _user: dict = Depends(get_current_user),
):
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if company_id:
        filters["company_id"] = company_id
    if segment:
        filters["segment"] = segment
    if engagement_stage:
        filters["engagement_stage"] = engagement_stage
    records = contacts_sheet.get_all(filters or None, limit=limit, offset=offset)

    if tag:
        records = [r for r in records if tag.lower() in r.get("tags", "").lower()]

    if not status_filter:
        records = [r for r in records if r.get("status") != "archived"]

    return records


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    response: Response,
    _user: dict = Depends(get_current_user),
):
    data = body.model_dump()
    # company_name wins over company_id when both are supplied — the resolved
    # value reflects intent more reliably than an opaque id the caller may have
    # picked up stale.
    name = data.pop("company_name", "")
    if name:
        data["company_id"] = resolve_or_create_company(companies_sheet, name)

    # Dedup guard: a re-add of someone already in the book (common when profiles
    # are pasted in overlapping batches) enriches the existing contact instead of
    # creating a duplicate. Match by linkedin_url, then email, then name.
    existing = find_duplicate_contact(
        contacts_sheet,
        linkedin_url=data.get("linkedin_url", ""),
        email=data.get("email", ""),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
    )
    if existing:
        updates = build_contact_enrichment(existing, data)
        record = contacts_sheet.update(existing["id"], updates) if updates else existing
        response.status_code = status.HTTP_200_OK
        return {**record, "deduped": True}

    record = contacts_sheet.create(data)
    return {**record, "deduped": False}


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    _user: dict = Depends(get_current_user),
):
    record = contacts_sheet.get_by_id(contact_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return record


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    body: ContactUpdate,
    _user: dict = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_none=True)
    name = update_data.pop("company_name", "")
    if name:
        update_data["company_id"] = resolve_or_create_company(companies_sheet, name)
    record = contacts_sheet.update(contact_id, update_data)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return record


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    _user: dict = Depends(get_current_user),
):
    if not contacts_sheet.delete(contact_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


@router.post("/from-linkedin", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_from_linkedin(
    body: ContactFromLinkedIn,
    _user: dict = Depends(get_current_user),
):
    # Deduplicate by linkedin_url
    existing = contacts_sheet.find_by_field("linkedin_url", body.linkedin_url)
    if existing:
        # Update existing contact with new data
        update_data = body.model_dump(exclude={"company_name"})
        update_data = {k: v for k, v in update_data.items() if v}
        # Ensure platform_handles includes linkedin
        handles = parse_platform_handles(existing.get("platform_handles", ""))
        handles["linkedin"] = body.linkedin_url
        update_data["platform_handles"] = json.dumps(handles)
        record = contacts_sheet.update(existing["id"], update_data)
        return record

    company_id = resolve_or_create_company(companies_sheet, body.company_name)

    record = contacts_sheet.create({
        "first_name": body.first_name,
        "last_name": body.last_name,
        "role": body.role,
        "linkedin_url": body.linkedin_url,
        "platform_handles": json.dumps({"linkedin": body.linkedin_url}),
        "email": body.email,
        "phone": body.phone,
        "notes": body.notes,
        "company_id": company_id,
        "source": "linkedin",
    })
    return record
