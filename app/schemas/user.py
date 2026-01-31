from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    referral_code: str  # Required for registration
    full_name: str

class UserLogin(UserBase):
    password: str

class UserUpdate(BaseModel):
    bot_chat_id: Optional[int] = None
    full_name: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    is_verified: bool
    role: str
    bot_chat_id: Optional[int] = None
    full_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
