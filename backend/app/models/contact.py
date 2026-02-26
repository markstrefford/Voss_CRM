from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    company_id: str = ""
    first_name: str = Field(..., min_length=1)
    last_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = ""
    linkedin_url: str = ""
    urls: str = ""
    source: str = "other"
    referral_contact_id: str = ""
    tags: str = ""
    notes: str = ""
    status: str = "active"
    segment: str = ""
    engagement_stage: str = "new"
    inbound_channel: str = ""
    do_not_contact: str = ""
    campaign_id: str = ""


class ContactUpdate(BaseModel):
    company_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    linkedin_url: str | None = None
    urls: str | None = None
    source: str | None = None
    referral_contact_id: str | None = None
    tags: str | None = None
    notes: str | None = None
    status: str | None = None
    segment: str | None = None
    engagement_stage: str | None = None
    inbound_channel: str | None = None
    do_not_contact: str | None = None
    campaign_id: str | None = None


class ContactFromLinkedIn(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = ""
    role: str = ""
    company_name: str = ""
    linkedin_url: str = Field(..., min_length=1)
    email: str = ""
    phone: str = ""


class Contact(BaseModel):
    id: str
    company_id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = ""
    linkedin_url: str = ""
    urls: str = ""
    source: str = ""
    referral_contact_id: str = ""
    tags: str = ""
    notes: str = ""
    status: str = "active"
    segment: str = ""
    engagement_stage: str = ""
    inbound_channel: str = ""
    do_not_contact: str = ""
    campaign_id: str = ""
    created_at: str = ""
    updated_at: str = ""
