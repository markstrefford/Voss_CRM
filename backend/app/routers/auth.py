from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.dependencies import get_current_user
from app.models import User, UserCreate, UserLogin
from app.services.sheet_service import users_sheet

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(body: UserLogin):
    user = users_sheet.find_by_field("username", body.username)
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": user["id"], "username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    if body.invite_code != settings.invite_code:
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
