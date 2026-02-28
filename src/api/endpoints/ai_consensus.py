"""Multi-Model AI Consensus API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.ai_consensus_service import AIConsensusService
router = APIRouter(prefix="/ai-consensus", tags=["ai-consensus"])

@router.get("/high-conviction")
async def get_high_conviction(min_confidence: float = Query(default=0.7, ge=0, le=1), max_disagreement: float = Query(default=0.3, ge=0, le=1), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get markets where multiple AI models strongly agree."""
    return await AIConsensusService(db).get_high_conviction(min_confidence=min_confidence, max_disagreement=max_disagreement, limit=limit)

@router.get("/most-disagreed")
async def get_most_disagreed(min_disagreement: float = Query(default=0.5, ge=0, le=1), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get markets where AI models disagree most (contrarian opportunities)."""
    return await AIConsensusService(db).get_most_disagreed(min_disagreement=min_disagreement, limit=limit)

@router.get("/{market_id}")
async def get_consensus(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get latest multi-model consensus for a market."""
    result = await AIConsensusService(db).get_consensus(market_id)
    return result or {"market_id": market_id, "message": "No consensus available. Generate one with POST."}

@router.post("/{market_id}/generate")
async def generate_consensus(market_id: str, market_price: Optional[float] = Query(default=None), db: AsyncSession = Depends(get_db)):
    """Generate multi-model AI consensus (ML ensemble + technical + sentiment + smart money)."""
    result = await AIConsensusService(db).generate_consensus(market_id, market_price=market_price)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to generate consensus")
    return result
