"""Semantic Market Clustering API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.market_cluster_service import MarketClusterService
router = APIRouter(prefix="/clusters", tags=["market-clusters"])

@router.get("")
async def get_clusters(limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get all discovered market clusters."""
    return await MarketClusterService(db).get_clusters(limit=limit)

@router.post("/discover")
async def discover_clusters(min_size: int = Query(default=2, ge=2), db: AsyncSession = Depends(get_db)):
    """Run AI-powered cluster discovery across active markets."""
    return await MarketClusterService(db).discover_clusters(min_cluster_size=min_size)

@router.get("/{cluster_id}")
async def get_cluster(cluster_id: int, db: AsyncSession = Depends(get_db)):
    """Get a cluster with all its market details."""
    result = await MarketClusterService(db).get_cluster(cluster_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return result

@router.get("/market/{market_id}")
async def find_market_clusters(market_id: str, db: AsyncSession = Depends(get_db)):
    """Find which clusters a market belongs to."""
    return await MarketClusterService(db).find_market_cluster(market_id)
