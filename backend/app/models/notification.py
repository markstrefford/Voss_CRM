from pydantic import BaseModel


class Notification(BaseModel):
    id: str = ""
    type: str = ""
    status: str = ""
    contact_id: str = ""
    company_id: str = ""
    title: str = ""
    body: str = ""
    payload: str = ""
    created_at: str = ""
    resolved_at: str = ""


class NotificationCreate(BaseModel):
    type: str
    contact_id: str
    company_id: str = ""
    title: str
    body: str = ""
    payload: str = "{}"


class NotificationResolve(BaseModel):
    action: str  # "accepted", "dismissed", "follow_up"
