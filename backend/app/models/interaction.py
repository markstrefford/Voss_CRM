from pydantic import BaseModel, Field


class InteractionCreate(BaseModel):
    contact_id: str = Field(..., min_length=1)
    deal_id: str = ""
    type: str = "note"
    subject: str = ""
    body: str = ""
    url: str = ""
    direction: str = "outbound"
    occurred_at: str = ""


class InteractionUpdate(BaseModel):
    contact_id: str | None = None
    deal_id: str | None = None
    type: str | None = None
    subject: str | None = None
    body: str | None = None
    url: str | None = None
    direction: str | None = None
    occurred_at: str | None = None


class Interaction(BaseModel):
    id: str
    contact_id: str = ""
    deal_id: str = ""
    type: str = ""
    subject: str = ""
    body: str = ""
    url: str = ""
    direction: str = ""
    occurred_at: str = ""
    created_at: str = ""
