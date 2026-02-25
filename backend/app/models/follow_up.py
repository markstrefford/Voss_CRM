from pydantic import BaseModel, Field


class FollowUpCreate(BaseModel):
    contact_id: str = Field(..., min_length=1)
    deal_id: str = ""
    title: str = Field(..., min_length=1)
    due_date: str = Field(..., min_length=1)
    due_time: str = ""
    status: str = "pending"
    notes: str = ""


class FollowUpSnooze(BaseModel):
    due_date: str = Field(..., min_length=1)
    due_time: str = ""


class FollowUp(BaseModel):
    id: str
    contact_id: str = ""
    deal_id: str = ""
    title: str = ""
    due_date: str = ""
    due_time: str = ""
    status: str = "pending"
    reminder_sent: str = "FALSE"
    notes: str = ""
    created_at: str = ""
    completed_at: str = ""
