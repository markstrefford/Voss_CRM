from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1)
    industry: str = ""
    website: str = ""
    size: str = ""
    notes: str = ""


class CompanyUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    website: str | None = None
    size: str | None = None
    notes: str | None = None


class Company(BaseModel):
    id: str
    name: str = ""
    industry: str = ""
    website: str = ""
    size: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
