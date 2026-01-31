from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from sqlalchemy import desc
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User, Alert, AlertLog
from app.schemas.alert import AlertCreate, AlertResponse

router = APIRouter()

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new alert rule.
    """
    alert_data = alert_in.model_dump()
    # Remove user_id from input if present, set manually
    new_alert = Alert(**alert_data)
    new_alert.user_id = current_user.id
    
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
        
    return new_alert

@router.get("/", response_model=List[AlertResponse])
async def read_alerts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve user's alerts.
    """
    statement = select(Alert).where(Alert.user_id == current_user.id).offset(skip).limit(limit)
    result = await db.execute(statement)
    alerts = result.scalars().all()
    return alerts

@router.get("/logs", response_model=Any)
async def read_alert_logs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve logs for all alerts of the user, ordered by latest.
    """
    statement = (
        select(AlertLog)
        .where(AlertLog.user_id == current_user.id)
        .order_by(desc(AlertLog.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    logs = result.scalars().all()
    return logs

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete an alert.
    Ensures the alert belongs to the current user.
    """
    statement = select(Alert).where(Alert.id == alert_id).where(Alert.user_id == current_user.id)
    result = await db.execute(statement)
    alert = result.scalar_one_or_none()
    
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Cascade delete logs (manual)
    # Note: Ideally handled by ON DELETE CASCADE in DB, but safety first here.
    from app.models import AlertLog
    log_statement = select(AlertLog).where(AlertLog.alert_id == alert.id)
    log_result = await db.execute(log_statement)
    logs = log_result.scalars().all()
    
    for log in logs:
        await db.delete(log)

    await db.delete(alert)
    await db.commit()
    return {"message": "Alert deleted successfully"}
