import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.dependencies import get_current_user
from app.limiter import limiter
from app.models import User, UserCreate, UserLogin
from app.services.sheet_service import users_sheet

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: UserLogin):
    client_ip = request.client.host if request.client else "unknown"
    user = users_sheet.find_by_field("username", body.username)
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        logger.warning(f"Failed login attempt for user={body.username!r} from ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    logger.info(f"Successful login for user={body.username!r} from ip={client_ip}")
    token = create_access_token({"sub": user["id"], "username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: UserCreate):
    client_ip = request.client.host if request.client else "unknown"
    if not hmac.compare_digest(body.invite_code, settings.invite_code):
        logger.warning(f"Failed registration (bad invite code) for user={body.username!r} from ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid invite code",
        )
    existing = users_sheet.find_by_field("username", body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = users_sheet.create({
        "username": body.username,
        "password_hash": hash_password(body.password),
    })
    logger.info(f"New user registered: user={body.username!r} from ip={client_ip}")
    token = create_access_token({"sub": user["id"], "username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def me(current_user: dict = Depends(get_current_user)):
    user = users_sheet.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return User(
        id=user["id"],
        username=user["username"],
        telegram_chat_id=user.get("telegram_chat_id", ""),
        created_at=user.get("created_at", ""),
    )
