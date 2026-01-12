"""API endpoints for alerts management."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...database.models import Alert, AlertHistory
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    """Alert creation model."""
    alert_type: str = Field(..., description="SIGNAL, PORTFOLIO, PREDICTION, CUSTOM")
    alert_rule: dict = Field(..., description="Rule configuration (JSON)")
    notification_method: str = Field(..., description="EMAIL, WEBHOOK, TELEGRAM, SMS")
    notification_target: str = Field(..., description="Email, webhook URL, Telegram chat ID, etc.")
    enabled: bool = Field(default=True)


class AlertResponse(BaseModel):
    """Alert response model."""
    id: int
    user_id: str
    alert_type: str
    alert_rule: dict
    notification_method: str
    notification_target: str
    enabled: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Alert history response model."""
    id: int
    alert_id: int
    signal_id: Optional[int]
    market_id: Optional[str]
    message: str
    sent_at: datetime
    success: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert."""
    try:
        db_alert = Alert(
            alert_type=alert.alert_type,
            alert_rule=alert.alert_rule,
            notification_method=alert.notification_method,
            notification_target=alert.notification_target,
            enabled=alert.enabled
        )
        db.add(db_alert)
        await db.commit()
        await db.refresh(db_alert)
        return AlertResponse.model_validate(db_alert)
    except Exception as e:
        logger.error("Failed to create alert", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    enabled: Optional[bool] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get all alerts."""
    try:
        query = select(Alert)
        if enabled is not None:
            query = query.where(Alert.enabled == enabled)
        if alert_type:
            query = query.where(Alert.alert_type == alert_type.upper())
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        return [AlertResponse.model_validate(a) for a in alerts]
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        return []


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Get alert by ID."""
    try:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")


@router.put("/{alert_id}/enable", response_model=AlertResponse)
async def enable_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Enable an alert."""
    try:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.enabled = True
        alert.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(alert)
        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to enable alert", alert_id=alert_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enable alert: {str(e)}")


@router.put("/{alert_id}/disable", response_model=AlertResponse)
async def disable_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Disable an alert."""
    try:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.enabled = False
        alert.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(alert)
        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to disable alert", alert_id=alert_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disable alert: {str(e)}")


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an alert."""
    try:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        await db.delete(alert)
        await db.commit()
        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert", alert_id=alert_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


@router.get("/{alert_id}/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    alert_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get alert history."""
    try:
        query = select(AlertHistory).where(
            AlertHistory.alert_id == alert_id
        ).order_by(
            AlertHistory.sent_at.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        history = result.scalars().all()
        return [AlertHistoryResponse.model_validate(h) for h in history]
    except Exception as e:
        logger.error("Failed to get alert history", alert_id=alert_id, error=str(e))
        return []

