from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    invite_code: str = Field(..., min_length=1)


class User(BaseModel):
    id: str
    username: str
    telegram_chat_id: str = ""
    created_at: str = ""
