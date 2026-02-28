"""Market Correlation Analysis API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.market_correlation_service import MarketCorrelationService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/correlations", tags=["correlations"])


class CorrelationRequest(BaseModel):
    market_id_a: str
    market_id_b: str
    lookback_hours: int = 168
    correlation_type: str = "price"


class MatrixRequest(BaseModel):
    market_ids: List[str]


@router.get("/top")
async def get_top_correlations(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get strongest correlations across all market pairs."""
    service = MarketCorrelationService(db)
    return await service.get_top_correlations(limit=limit)


@router.get("/{market_id}")
async def find_correlated_markets(
    market_id: str,
    min_correlation: float = Query(default=0.5, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Find markets correlated with a given market."""
    service = MarketCorrelationService(db)
    return await service.find_correlated_markets(market_id, min_correlation=min_correlation, limit=limit)


@router.post("/compute")
async def compute_correlation(request: CorrelationRequest, db: AsyncSession = Depends(get_db)):
    """Compute correlation between two markets."""
    service = MarketCorrelationService(db)
    result = await service.compute_correlation(
        market_id_a=request.market_id_a,
        market_id_b=request.market_id_b,
        lookback_hours=request.lookback_hours,
        correlation_type=request.correlation_type,
    )
    if not result:
        return {"message": "Insufficient data to compute correlation"}
    return result


@router.post("/matrix")
async def get_correlation_matrix(request: MatrixRequest, db: AsyncSession = Depends(get_db)):
    """Get correlation matrix for a set of markets."""
    if len(request.market_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 markets for matrix")
    service = MarketCorrelationService(db)
    return await service.get_correlation_matrix(request.market_ids)
