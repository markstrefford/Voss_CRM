from pydantic import BaseModel, Field


class DealCreate(BaseModel):
    contact_id: str = ""
    company_id: str = ""
    title: str = Field(..., min_length=1)
    stage: str = "lead"
    value: str = ""
    currency: str = "USD"
    priority: str = "medium"
    expected_close: str = ""
    notes: str = ""


class DealUpdate(BaseModel):
    contact_id: str | None = None
    company_id: str | None = None
    title: str | None = None
    stage: str | None = None
    value: str | None = None
    currency: str | None = None
    priority: str | None = None
    expected_close: str | None = None
    notes: str | None = None


class DealStageUpdate(BaseModel):
    stage: str = Field(..., pattern=r"^(lead|prospect|qualified|proposal|negotiation|won|lost)$")


class Deal(BaseModel):
    id: str
    contact_id: str = ""
    company_id: str = ""
    title: str = ""
    stage: str = "lead"
    value: str = ""
    currency: str = "USD"
    priority: str = "medium"
    expected_close: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
