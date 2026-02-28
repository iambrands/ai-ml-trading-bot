"""Insider / Suspicious Activity Detection API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.insider_detection_service import InsiderDetectionService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/insider-detection", tags=["insider-detection"])


@router.get("/alerts")
async def get_suspicious_alerts(
    severity: Optional[str] = None,
    activity_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get recent suspicious activity alerts."""
    service = InsiderDetectionService(db)
    return await service.get_recent_alerts(severity=severity, activity_type=activity_type, limit=limit)


@router.post("/scan")
async def scan_for_suspicious_activity(
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Run a suspicious activity scan."""
    service = InsiderDetectionService(db)
    return await service.scan_for_suspicious_activity(hours=hours)


@router.get("/wallets")
async def get_suspicious_wallets(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get wallets with the most suspicious activity."""
    service = InsiderDetectionService(db)
    return await service.get_suspicious_wallets(limit=limit)


@router.get("/risk/{market_id}")
async def get_market_risk_score(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get risk score for a market based on suspicious activity."""
    service = InsiderDetectionService(db)
    return await service.get_market_risk_score(market_id)


@router.put("/review/{activity_id}")
async def mark_as_reviewed(activity_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a suspicious activity as reviewed."""
    service = InsiderDetectionService(db)
    success = await service.mark_reviewed(activity_id)
    return {"status": "reviewed" if success else "not_found", "activity_id": activity_id}
