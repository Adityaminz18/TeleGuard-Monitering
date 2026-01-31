from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User, TelegramSession
from app.schemas.telegram import TelegramAuthRequest, TelegramAuthResponse, TelegramVerifyRequest, TelegramVerifyResponse
from app.services.telegram_service import telegram_service

router = APIRouter()

@router.post("/request-code", response_model=TelegramAuthResponse)
async def request_telegram_code(
    payload: TelegramAuthRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Initiate Telegram login. Sends OTP to the provided phone number.
    Returns phone_code_hash which is needed for verification.
    """
    try:
        phone_code_hash, session_string = await telegram_service.send_code(payload.phone_number)
        return {
            "phone_number": payload.phone_number,
            "phone_code_hash": phone_code_hash,
            "session_string": session_string,
            "message": "OTP sent successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-code", response_model=TelegramVerifyResponse)
async def verify_telegram_code(
    payload: TelegramVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Complete Telegram login with OTP.
    Saves session string to database.
    """
    try:
        session_string, telegram_user_id, username = await telegram_service.verify_code(
            phone_number=payload.phone_number,
            code=payload.code,
            phone_code_hash=payload.phone_code_hash,
            session_string=payload.session_string,
            password=payload.password
        )
        
        # Save to DB
        # Check if session exists for user
        statement = select(TelegramSession).where(TelegramSession.user_id == current_user.id)
        result = await db.execute(statement)
        existing_session = result.scalar_one_or_none()
        
        if existing_session:
            existing_session.session_string = session_string
            existing_session.phone_number = payload.phone_number
            existing_session.telegram_id = str(telegram_user_id)
            existing_session.is_active = True
            db.add(existing_session)
        else:
            new_session = TelegramSession(
                user_id=current_user.id,
                session_string=session_string,
                phone_number=payload.phone_number,
                telegram_id=str(telegram_user_id),
                is_active=True
            )
            db.add(new_session)
        
        await db.commit()
        
        return {
            "message": "Telegram account connected successfully",
            "session_id": str(telegram_user_id)
        }
        
    except ValueError as ve:
        # Likely 2FA error
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dialogs")
async def get_telegram_dialogs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Fetch recent Telegram chats for the current user.
    """
    # Fetch active session
    statement = select(TelegramSession).where(TelegramSession.user_id == current_user.id).where(TelegramSession.is_active == True)
    result = await db.execute(statement)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=400, detail="No active Telegram session found. Please connect first.")
        
    try:
        # Read from Cache (Synced by Worker)
        from app.models import TelegramChat
        stmt = select(TelegramChat).where(TelegramChat.user_id == current_user.id).order_by(desc(TelegramChat.created_at))
        res = await db.execute(stmt)
        dialogs = res.scalars().all()
        
        if not dialogs:
           return []
            
        return dialogs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
