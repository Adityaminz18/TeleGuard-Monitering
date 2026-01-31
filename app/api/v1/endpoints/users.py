from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User, TelegramSession

router = APIRouter()

@router.get("/me")
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user profile and telegram connection status.
    """
    # Check if telegram session exists
    # ORM Approach: We could use lazy loading provided by SQLModel relationships: `current_user.sessions`
    # But since it's async, we need specific loading options or explicit queries.
    # Let's use an explicit query for clarity.
    
    statement = select(TelegramSession).where(TelegramSession.user_id == current_user.id).where(TelegramSession.is_active == True)
    result = await db.execute(statement)
    telegram_session = result.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "telegram_connected": bool(telegram_session),
        "telegram_phone": telegram_session.phone_number if telegram_session else None,
        "bot_chat_id": current_user.bot_chat_id,
        "full_name": current_user.full_name
    }

from app.schemas.user import UserUpdate, UserResponse

@router.put("/me")
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update user settings.
    """
    if user_in.bot_chat_id is not None:
        current_user.bot_chat_id = user_in.bot_chat_id
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
        
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

from app.api.dependencies import get_current_admin_user

@router.get("/admin-only", dependencies=[Depends(get_current_admin_user)])
async def admin_only_route():
    """
    Test endpoint for Admin role.
    """
    return {"message": "Hello Admin!"}

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve all users (Admin only).
    """
    statement = select(User).offset(skip).limit(limit)
    result = await db.execute(statement)
    users = result.scalars().all()
    return users
