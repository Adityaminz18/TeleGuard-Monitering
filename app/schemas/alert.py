from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AlertBase(BaseModel):
    source_id: Optional[int] = None # Telegram Chat ID (NULL for global)
    source_name: Optional[str] = "All Chats"
    keywords: List[str] = []
    excluded_keywords: List[str] = []
    is_regex: bool = False
    
    notify_email: bool = True
    notify_bot: bool = False
    webhook_url: Optional[str] = None
    is_paused: bool = False

class AlertCreate(AlertBase):
    pass

class AlertUpdate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    trigger_count: int = 0
    
    class Config:
        from_attributes = True
