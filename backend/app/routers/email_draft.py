from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.services.claude_service import draft_email

router = APIRouter(prefix="/api/email", tags=["email"])


class EmailDraftRequest(BaseModel):
    contact_id: str = Field(..., min_length=1)
    deal_id: str | None = None
    intent: str = Field(..., min_length=1)
    tone: str = "professional"


class EmailDraftResponse(BaseModel):
    subject: str
    body: str


@router.post("/draft", response_model=EmailDraftResponse)
async def generate_email_draft(
    body: EmailDraftRequest,
    _user: dict = Depends(get_current_user),
):
    try:
        result = draft_email(
            contact_id=body.contact_id,
            deal_id=body.deal_id,
            intent=body.intent,
            tone=body.tone,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate email draft: {str(e)}",
        )
