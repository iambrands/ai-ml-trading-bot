"""API endpoints for prediction generation and processing."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db
from ...trading.auto_processor import AutoProcessor
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/generate")
async def generate_predictions_endpoint(
    limit: int = 10,
    auto_signals: bool = True,
    auto_trades: bool = False,
    background_tasks: BackgroundTasks,
):
    """
    Generate predictions for active markets.
    
    This endpoint triggers the prediction generation process which:
    - Fetches active markets
    - Generates predictions using trained models
    - Optionally generates signals and trades automatically
    
    Args:
        limit: Number of markets to process
        auto_signals: Automatically generate signals from predictions
        auto_trades: Automatically create trades from signals
        background_tasks: FastAPI background tasks (always injected by FastAPI)
    """
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from scripts.generate_predictions import generate_predictions
        
        # Always run in background to avoid timeout
        # Prediction generation can take 2-5 minutes, so we return immediately
        background_tasks.add_task(
            generate_predictions,
            limit=limit,
            auto_generate_signals=auto_signals,
            auto_create_trades=auto_trades,
        )
        return {
            "status": "started",
            "message": "Prediction generation started in background",
            "limit": limit,
            "auto_signals": auto_signals,
            "auto_trades": auto_trades,
        }
    except Exception as e:
        logger.error("Failed to start prediction generation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start prediction generation: {str(e)}")


@router.post("/process/{prediction_id}")
async def process_prediction_endpoint(
    prediction_id: int,
    auto_signals: bool = True,
    auto_trades: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Process an existing prediction into signals and trades.
    
    Args:
        prediction_id: ID of the prediction to process
        auto_signals: Generate signal from prediction
        auto_trades: Create trade from signal
        db: Database session
    """
    try:
        from sqlalchemy import select
        from ...database.models import Prediction, Market as DBMarket
        from ...data.models import Market
        from ...models.ensemble import EnsemblePrediction
        
        # Get prediction
        result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
        db_prediction = result.scalar_one_or_none()
        
        if not db_prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        # Get market
        result = await db.execute(select(DBMarket).where(DBMarket.market_id == db_prediction.market_id))
        db_market = result.scalar_one_or_none()
        
        if not db_market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Create Market object
        market = Market(
            id=db_market.market_id,
            condition_id=db_market.condition_id,
            question=db_market.question,
            category=db_market.category,
            resolution_date=db_market.resolution_date,
            outcome=db_market.outcome,
            yes_price=float(db_prediction.market_price),
            no_price=1.0 - float(db_prediction.market_price),
        )
        
        # Create EnsemblePrediction
        model_predictions = db_prediction.model_predictions if db_prediction.model_predictions else {}
        ensemble_pred = EnsemblePrediction(
            probability=float(db_prediction.model_probability),
            confidence=float(db_prediction.confidence),
            model_predictions=model_predictions,
        )
        
        # Process prediction
        processor = AutoProcessor(auto_signals=auto_signals, auto_trades=auto_trades)
        signals_created, trades_created = await processor.process_prediction(market, ensemble_pred, db_prediction, db)
        
        return {
            "status": "success",
            "prediction_id": prediction_id,
            "signals_created": signals_created,
            "trades_created": trades_created,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process prediction", prediction_id=prediction_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process prediction: {str(e)}")

