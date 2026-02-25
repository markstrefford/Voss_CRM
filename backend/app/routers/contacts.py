from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models import Contact, ContactCreate, ContactFromLinkedIn, ContactUpdate
from app.services.sheet_service import companies_sheet, contacts_sheet

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
async def list_contacts(
    q: str | None = Query(None),
    tag: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    company_id: str | None = Query(None),
    _user: dict = Depends(get_current_user),
):
    if q:
        records = contacts_sheet.search(q, ["first_name", "last_name", "email", "company_id", "tags", "notes"])
    else:
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if company_id:
            filters["company_id"] = company_id
        records = contacts_sheet.get_all(filters or None)

    if tag:
        records = [r for r in records if tag.lower() in r.get("tags", "").lower()]

    # Exclude archived unless specifically requested
    if not status_filter:
        records = [r for r in records if r.get("status") != "archived"]

    return records


@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    _user: dict = Depends(get_current_user),
):
    record = contacts_sheet.create(body.model_dump())
    return record


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
        record = contacts_sheet.update(existing["id"], update_data)
        return record

    # Resolve company
    company_id = ""
    if body.company_name:
        company = companies_sheet.find_by_field("name", body.company_name)
        if company:
            company_id = company["id"]
        else:
            new_company = companies_sheet.create({"name": body.company_name})
            company_id = new_company["id"]

    record = contacts_sheet.create({
        "first_name": body.first_name,
        "last_name": body.last_name,
        "role": body.role,
        "linkedin_url": body.linkedin_url,
        "email": body.email,
        "phone": body.phone,
        "company_id": company_id,
        "source": "linkedin",
    })
    return record
