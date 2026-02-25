from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models import Company, CompanyCreate, CompanyUpdate
from app.services.sheet_service import companies_sheet, contacts_sheet

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[Company])
async def list_companies(_user: dict = Depends(get_current_user)):
    return companies_sheet.get_all()


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    _user: dict = Depends(get_current_user),
):
    return companies_sheet.create(body.model_dump())


@router.get("/{company_id}")
async def get_company(
    company_id: str,
    _user: dict = Depends(get_current_user),
):
    record = companies_sheet.get_by_id(company_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company_contacts = contacts_sheet.get_all({"company_id": company_id})
    return {**record, "contacts": company_contacts}


@router.put("/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    body: CompanyUpdate,
    _user: dict = Depends(get_current_user),
):
    update_data = body.model_dump(exclude_none=True)
    record = companies_sheet.update(company_id, update_data)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return record
