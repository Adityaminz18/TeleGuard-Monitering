from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, ARRAY, String, Text, BigInteger

# Shared Properties
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str
    referral_code_used: Optional[str] = None
    is_verified: bool = False
    role: str = "user"
    full_name: Optional[str] = Field(default=None, sa_column=Column(String))
    bot_chat_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["TelegramSession"] = Relationship(back_populates="user")
    alerts: List["Alert"] = Relationship(back_populates="user")

class ReferralCode(SQLModel, table=True):
    __tablename__ = "referral_codes"
    code: str = Field(primary_key=True)
    created_by_user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    max_uses: int = 10
    used_count: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TelegramSession(SQLModel, table=True):
    __tablename__ = "telegram_sessions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    telegram_id: Optional[int] = Field(default=None, sa_column=Column(String)) # Store as string to be safe, or BigInt
    session_string: str
    phone_number: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="sessions")

class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    source_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    source_name: Optional[str] = "All Chats"
    
    # Text[] in Postgres requires specific SA definition
    keywords: List[str] = Field(default=[], sa_column=Column(ARRAY(Text)))
    excluded_keywords: List[str] = Field(default=[], sa_column=Column(ARRAY(Text)))
    
    is_regex: bool = False
    notify_email: bool = True
    notify_bot: bool = False
    webhook_url: Optional[str] = None
    is_paused: bool = False
    trigger_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="alerts")

class AlertLog(SQLModel, table=True):
    __tablename__ = "alert_logs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    alert_id: Optional[UUID] = Field(default=None, foreign_key="alerts.id")
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    message_content: Optional[str] = None
    detected_keyword: Optional[str] = None
    dispatched_to_email: bool = False
    dispatched_to_bot: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
