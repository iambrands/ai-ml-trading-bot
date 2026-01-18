"""FastAPI application for trading bot API."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from ..data.sources.polymarket import PolymarketDataSource
from ..database import get_db, init_db
from ..database.connection import AsyncSessionLocal, get_pool_stats
from ..database.models import Market, Prediction, Signal, Trade, PortfolioSnapshot
from ..utils.logging import configure_logging, get_logger
from .cache import cache_response

# Import endpoints (with error handling for optional modules)
try:
    from .endpoints import predictions as predictions_endpoints
except ImportError:
    predictions_endpoints = None

try:
    from .endpoints import ai_analysis as ai_analysis_endpoints
except ImportError:
    ai_analysis_endpoints = None

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database initialization failed (this is OK if DB is not set up yet)", error=str(e))
    logger.info("API server starting...")
    yield
    # Shutdown
    logger.info("API server shutting down...")


app = FastAPI(
    title="Polymarket AI Trading Bot API",
    description="REST API for AI-powered Polymarket trading bot",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (UI)
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Landing page route
@app.get("/")
async def landing():
    """Redirect to landing page."""
    from fastapi.responses import FileResponse
    landing_path = os.path.join(static_dir, "landing.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    # Fallback to dashboard if landing page doesn't exist
    dashboard_path = os.path.join(static_dir, "index.html")
    return FileResponse(dashboard_path)

# Dashboard route
@app.get("/dashboard")
async def dashboard():
    """Serve dashboard page."""
    from fastapi.responses import FileResponse
    dashboard_path = os.path.join(static_dir, "index.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Dashboard not found")

# Include API routers
if predictions_endpoints:
    app.include_router(predictions_endpoints.router)
if ai_analysis_endpoints:
    app.include_router(ai_analysis_endpoints.router)

# Include new feature routers
try:
    from .endpoints import alerts as alerts_endpoints
    app.include_router(alerts_endpoints.router)
except ImportError:
    logger.warning("Alerts endpoints not available")

try:
    from .endpoints import paper_trading as paper_trading_endpoints
    app.include_router(paper_trading_endpoints.router)
except ImportError:
    logger.warning("Paper trading endpoints not available")

try:
    from .endpoints import analytics as analytics_endpoints
    app.include_router(analytics_endpoints.router)
except ImportError:
    logger.warning("Analytics endpoints not available")

try:
    from .endpoints import arbitrage as arbitrage_endpoints
    app.include_router(arbitrage_endpoints.router)
except ImportError:
    logger.warning("Arbitrage endpoints not available")

try:
    from .endpoints import dashboard as dashboard_endpoints
    app.include_router(dashboard_endpoints.router)
except ImportError:
    logger.warning("Dashboard endpoints not available")


# Pydantic models for API responses
class MarketResponse(BaseModel):
    """Market response model."""

    id: int
    market_id: str
    condition_id: str
    question: str
    category: Optional[str]
    resolution_date: Optional[datetime]
    outcome: Optional[str]
    yes_price: Optional[float] = None  # From latest prediction or live API
    no_price: Optional[float] = None  # From latest prediction or live API
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    """Prediction response model."""

    id: int
    market_id: str
    prediction_time: datetime
    model_probability: float
    market_price: float
    edge: float
    confidence: float
    model_version: str
    model_predictions: Optional[dict]

    class Config:
        from_attributes = True


class SignalResponse(BaseModel):
    """Signal response model."""

    id: int
    market_id: str
    side: str
    signal_strength: str
    suggested_size: Optional[float]
    executed: bool
    edge: Optional[float] = None  # Edge from associated prediction
    created_at: datetime

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    """Trade response model."""

    id: int
    market_id: str
    side: str
    entry_price: float
    size: float
    exit_price: Optional[float]
    pnl: Optional[float]
    status: str
    entry_time: datetime
    exit_time: Optional[datetime]

    class Config:
        from_attributes = True


class PortfolioSnapshotResponse(BaseModel):
    """Portfolio snapshot response model."""

    id: int
    snapshot_time: datetime
    total_value: float
    cash: float
    positions_value: float
    total_exposure: float
    daily_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    realized_pnl: Optional[float]

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str = "0.1.0"


# API Endpoints


@app.get("/")
async def root():
    """Root endpoint - serve UI or redirect."""
    # Try to serve the UI if it exists
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    # Otherwise return health check
    return HealthResponse(status="healthy", timestamp=datetime.now(timezone.utc))


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon or return 204 No Content."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    favicon_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        from fastapi.responses import FileResponse
        return FileResponse(favicon_path)
    # Return 204 No Content instead of 404
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health")
@cache_response(seconds=30)  # Cache for 30 seconds - health checks don't need real-time
async def health():
    """Comprehensive health check for all system components."""
    from fastapi import status
    from fastapi.responses import JSONResponse
    from ..database.connection import get_pool_stats, engine
    from ..config.settings import get_settings
    
    checks = {}
    # Only critical systems affect health status
    # Prediction age and other informational checks don't cause failures
    critical_healthy = True
    
    # Check database (CRITICAL)
    try:
        if engine:
            # Test query
            async with AsyncSessionLocal() as session:
                await session.execute(select(1))
            
            # Get pool stats
            pool_stats = get_pool_stats()
            if pool_stats:
                pool_usage = pool_stats.get("utilization", 0)
                # Only mark as degraded if pool usage is very high (>95%)
                is_degraded = pool_usage >= 0.95
                checks["database"] = {
                    "status": "healthy" if not is_degraded else "degraded",
                    "pool_usage": f"{pool_usage:.1%}",
                    "connections": pool_stats,
                    "warning": f"High pool usage: {pool_usage:.1%}" if pool_usage >= 0.8 else None
                }
                if pool_usage >= 0.8:
                    logger.warning("High database pool utilization", usage=f"{pool_usage:.1%}")
                # Only fail health check if pool is critically exhausted
                if pool_usage >= 0.95:
                    critical_healthy = False
            else:
                checks["database"] = {"status": "healthy", "pool_stats": "unavailable"}
        else:
            checks["database"] = {"status": "unavailable", "message": "Database not configured"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        critical_healthy = False
    
    # Check recent predictions
    try:
        if engine:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Prediction.created_at)
                    .order_by(desc(Prediction.created_at))
                    .limit(1)
                )
                last_pred = result.scalar_one_or_none()
                
                if last_pred:
                    # Convert to timezone-aware for comparison, then calculate age
                    now_aware = datetime.now(timezone.utc)
                    last_pred_aware = last_pred.replace(tzinfo=timezone.utc) if last_pred.tzinfo is None else last_pred
                    age_minutes = (now_aware - last_pred_aware).total_seconds() / 60
                    
                    # Predictions freshness is informational, not critical for health
                    # Predictions are valid for hours/days, not just minutes
                    # Only warn if predictions are very old (>24 hours), but don't fail health check
                    is_very_old = age_minutes >= 1440  # 24 hours
                    checks["recent_predictions"] = {
                        "status": "ok",  # Always OK if predictions exist
                        "last_prediction": last_pred.isoformat(),
                        "age_minutes": round(age_minutes, 1),
                        "age_hours": round(age_minutes / 60, 1),
                        "warning": f"Predictions are {round(age_minutes / 60, 1)} hours old" if is_very_old else None,
                        "note": "Predictions refresh periodically via cron job"
                    }
                    # Don't mark unhealthy based on prediction age - predictions are still valid
                    # Only fail if critical systems (DB, models) are down
                else:
                    checks["recent_predictions"] = {
                        "status": "no_predictions", 
                        "message": "No predictions found yet (system may be starting up)"
                    }
                    # Don't fail health check if no predictions yet - system might be starting up
        else:
            checks["recent_predictions"] = {"status": "unavailable", "message": "Database not configured"}
    except Exception as e:
        checks["recent_predictions"] = {"status": "error", "error": str(e)}
        # Don't fail health check for prediction check errors - informational only
    
    # Check paper trading mode
    try:
        settings = get_settings()
        paper_trading = getattr(settings, 'paper_trading_mode', True)
        checks["paper_trading"] = {
            "status": "healthy",
            "paper_trading_enabled": paper_trading,
            "warning": None if paper_trading else "LIVE TRADING IS ENABLED"
        }
    except Exception as e:
        checks["paper_trading"] = {"status": "unhealthy", "error": str(e)}
    
    # Check model files
    try:
        import os
        from pathlib import Path
        
        # Try multiple possible paths
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "models" / "xgboost_model.pkl",
            Path("/app/data/models/xgboost_model.pkl"),  # Railway/Docker path
            Path("data/models/xgboost_model.pkl"),  # Relative path
        ]
        
        model_path = None
        model_exists = False
        for path in possible_paths:
            if path.exists():
                model_path = str(path)
                model_exists = True
                break
        
        if not model_path:
            model_path = str(possible_paths[0])  # Use first as default for display
        
        checks["model_loaded"] = {
            "status": "healthy" if model_exists else "unavailable",
            "model_path": model_path,
            "exists": model_exists,
            "checked_paths": [str(p) for p in possible_paths]
        }
    except Exception as e:
        checks["model_loaded"] = {"status": "unhealthy", "error": str(e)}
        # Model loading is critical - fail health check if unavailable
        critical_healthy = False
    
    # Only return 503 if critical systems (DB, models) are down
    # Prediction age and other informational checks don't affect health status
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "healthy" if critical_healthy else "degraded",
        "checks": checks
    }
    
    http_status = status.HTTP_200_OK if critical_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=results, status_code=http_status)


@app.get("/markets", response_model=List[MarketResponse])
@cache_response(seconds=30)  # Cache for 30 seconds - markets don't change frequently
async def get_markets(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    outcome: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get list of markets with prices from latest predictions."""
    try:
        from sqlalchemy.orm import joinedload
        
        from datetime import timedelta
        
        # RELAXED: Filter out markets that ended more than 30 days ago (not just 1 day)
        # This allows recently resolved markets to be shown
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        query = select(Market).where(
            # Only include markets that haven't ended yet, or ended recently (<30 days ago)
            (Market.resolution_date.is_(None)) | (Market.resolution_date >= cutoff_date)
        )
        
        if outcome:
            query = query.where(Market.outcome == outcome.upper())
        
        query = query.order_by(desc(Market.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        markets = result.scalars().all()
        
        # OPTIMIZED: Get latest predictions for all markets in a single query (no N+1)
        market_responses = []
        market_ids = [m.market_id for m in markets]
        
        # Get latest prediction for each market using window function approach (single query)
        from sqlalchemy import func, distinct
        from sqlalchemy.sql import literal
        
        if market_ids:
            # Use a subquery to get the latest prediction time per market
            latest_pred_times = (
                select(
                    Prediction.market_id,
                    func.max(Prediction.prediction_time).label('max_time')
                )
                .where(Prediction.market_id.in_(market_ids))
                .group_by(Prediction.market_id)
                .subquery()
            )
            
            # Join to get the actual prediction rows
            predictions_query = (
                select(Prediction)
                .join(
                    latest_pred_times,
                    (Prediction.market_id == latest_pred_times.c.market_id) &
                    (Prediction.prediction_time == latest_pred_times.c.max_time)
                )
            )
            
            pred_result = await db.execute(predictions_query)
            predictions_dict = {p.market_id: p for p in pred_result.scalars().all()}
        else:
            predictions_dict = {}
        
        # Try to fetch live prices for markets without predictions (optional, non-blocking)
        live_markets_map = {}
        try:
            async with PolymarketDataSource() as polymarket:
                live_markets = await polymarket.fetch_active_markets(limit=limit * 2)
                live_markets_map = {m.id: m for m in live_markets}
        except Exception as e:
            logger.debug("Failed to fetch live markets for price fallback", error=str(e))
        
        # Build responses (no per-market queries needed)
        for market in markets:
            latest_pred = predictions_dict.get(market.market_id)
            
            # Get prices from prediction or live market data
            yes_price = None
            no_price = None
            
            if latest_pred:
                yes_price = float(latest_pred.market_price)
                no_price = 1.0 - yes_price
            elif market.market_id in live_markets_map:
                # Fallback to live market data
                live_market = live_markets_map[market.market_id]
                if live_market.yes_price > 0:
                    yes_price = float(live_market.yes_price)
                    no_price = float(live_market.no_price)
            
            # Build response with prices
            live_market = live_markets_map.get(market.market_id) if market.market_id in live_markets_map else None
            market_dict = {
                "id": market.id,
                "market_id": market.market_id,
                "condition_id": market.condition_id,
                "question": market.question,
                "category": market.category or (live_market.category if live_market else None),
                "resolution_date": market.resolution_date,
                "outcome": market.outcome,
                "yes_price": yes_price,
                "no_price": no_price,
                "created_at": market.created_at,
                "resolved_at": market.resolved_at,
            }
            market_responses.append(MarketResponse(**market_dict))
        
        return market_responses
    except Exception as e:
        logger.warning("Database connection failed, returning empty list", error=str(e))
        return []  # Return empty list if DB not available


@app.get("/markets/{market_id}", response_model=MarketResponse)
async def get_market(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get market by ID with prices from latest prediction or live API."""
    try:
        result = await db.execute(select(Market).where(Market.market_id == market_id))
        market = result.scalar_one_or_none()
        
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Get latest prediction for prices
        pred_query = select(Prediction).where(
            Prediction.market_id == market.market_id
        ).order_by(desc(Prediction.prediction_time)).limit(1)
        
        pred_result = await db.execute(pred_query)
        latest_pred = pred_result.scalar_one_or_none()
        
        # Try to get live prices if no prediction
        yes_price = None
        no_price = None
        category = market.category
        
        if latest_pred:
            yes_price = float(latest_pred.market_price)
            no_price = 1.0 - yes_price
        else:
            # Fallback to live market data
            try:
                async with PolymarketDataSource() as polymarket:
                    live_market = await polymarket.fetch_market(market.market_id)
                    if live_market and live_market.yes_price > 0:
                        yes_price = float(live_market.yes_price)
                        no_price = float(live_market.no_price)
                        if not category:
                            category = live_market.category
            except Exception as e:
                logger.debug("Failed to fetch live market for price", market_id=market.market_id, error=str(e))
        
        # Build response with prices
        market_dict = {
            "id": market.id,
            "market_id": market.market_id,
            "condition_id": market.condition_id,
            "question": market.question,
            "category": category,
            "resolution_date": market.resolution_date,
            "outcome": market.outcome,
            "yes_price": yes_price,
            "no_price": no_price,
            "created_at": market.created_at,
            "resolved_at": market.resolved_at,
        }
        
        return MarketResponse(**market_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Database connection failed", error=str(e))
        raise HTTPException(status_code=503, detail="Database not available")


@app.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(
    market_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get model predictions."""
    try:
        query = select(Prediction)
        
        if market_id:
            query = query.where(Prediction.market_id == market_id)
        
        query = query.order_by(desc(Prediction.prediction_time)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        predictions = result.scalars().all()
        
        return [PredictionResponse.model_validate(p) for p in predictions]
    except Exception as e:
        logger.warning("Database connection failed, returning empty list", error=str(e))
        return []  # Return empty list if DB not available


@app.get("/signals", response_model=List[SignalResponse])
async def get_signals(
    market_id: Optional[str] = Query(default=None),
    executed: Optional[bool] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get trading signals."""
    try:
        # Join with Prediction to get edge
        from sqlalchemy.orm import joinedload
        
        query = select(Signal).options(joinedload(Signal.prediction))
        
        if market_id:
            query = query.where(Signal.market_id == market_id)
        if executed is not None:
            query = query.where(Signal.executed == executed)
        
        query = query.order_by(desc(Signal.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        signals = result.unique().scalars().all()
        
        # Build response with edge from prediction
        signal_responses = []
        for signal in signals:
            signal_dict = {
                "id": signal.id,
                "market_id": signal.market_id,
                "side": signal.side,
                "signal_strength": signal.signal_strength,
                "suggested_size": float(signal.suggested_size) if signal.suggested_size else None,
                "executed": signal.executed,
                "created_at": signal.created_at,
                "edge": float(signal.prediction.edge) if signal.prediction else None,
            }
            signal_responses.append(SignalResponse(**signal_dict))
        
        return signal_responses
    except Exception as e:
        logger.warning("Database connection failed, returning empty list", error=str(e))
        return []  # Return empty list if DB not available


@app.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    market_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get trades."""
    try:
        query = select(Trade)
        
        if market_id:
            query = query.where(Trade.market_id == market_id)
        if status:
            query = query.where(Trade.status == status.upper())
        
        query = query.order_by(desc(Trade.entry_time)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        trades = result.scalars().all()
        
        return [TradeResponse.model_validate(t) for t in trades]
    except Exception as e:
        logger.warning("Database connection failed, returning empty list", error=str(e))
        return []  # Return empty list if DB not available


@app.get("/portfolio/snapshots", response_model=List[PortfolioSnapshotResponse])
async def get_portfolio_snapshots(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio snapshots."""
    try:
        query = select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.snapshot_time)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        snapshots = result.scalars().all()
        
        return [PortfolioSnapshotResponse.model_validate(s) for s in snapshots]
    except Exception as e:
        logger.warning("Database connection failed, returning empty list", error=str(e))
        return []  # Return empty list if DB not available


@app.get("/portfolio/latest", response_model=PortfolioSnapshotResponse)
async def get_latest_portfolio_snapshot(db: AsyncSession = Depends(get_db)):
    """Get latest portfolio snapshot."""
    try:
        query = select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.snapshot_time)).limit(1)
        
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()
        
        if not snapshot:
            raise HTTPException(status_code=404, detail="No portfolio snapshot found")
        
        return PortfolioSnapshotResponse.model_validate(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Database connection failed, returning 404", error=str(e))
        # Return 404 instead of 503 so UI can handle it gracefully
        raise HTTPException(status_code=404, detail="No portfolio snapshot found (database may not be set up)")


# Live data endpoints (fetch from APIs, not database)
@app.get("/live/markets", response_model=List[dict])
async def get_live_markets(limit: int = Query(default=50, ge=1, le=100)):
    """Get live markets from Polymarket API with real-time prices."""
    try:
        async with PolymarketDataSource() as polymarket:
            markets = await polymarket.fetch_active_markets(limit=limit)
            return [
                {
                    "market_id": m.id,
                    "condition_id": m.condition_id,
                    "question": m.question,
                    "category": m.category,
                    "yes_price": float(m.yes_price) if m.yes_price > 0 else None,
                    "no_price": float(m.no_price) if m.no_price > 0 else None,
                    "volume_24h": float(m.volume_24h) if m.volume_24h > 0 else None,
                    "liquidity": float(m.liquidity) if m.liquidity > 0 else None,
                    "outcome": m.outcome,
                    "resolution_date": m.resolution_date.isoformat() if m.resolution_date else None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                for m in markets
            ]
    except Exception as e:
        logger.error("Failed to fetch live markets", error=str(e))
        return []


@app.get("/live/market/{market_id}", response_model=dict)
async def get_live_market(market_id: str):
    """Get live market data from Polymarket API."""
    try:
        async with PolymarketDataSource() as polymarket:
            market = await polymarket.fetch_market(market_id)
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            
            market_data = await polymarket.fetch_market_data(market_id)
            
            return {
                "market_id": market.id,
                "condition_id": market.condition_id,
                "question": market.question,
                "category": market.category,
                "yes_price": float(market.yes_price),
                "no_price": float(market.no_price),
                "outcome": market.outcome,
                "resolution_date": market.resolution_date.isoformat() if market.resolution_date else None,
                "bid_price": float(market_data.bid_price) if market_data else None,
                "ask_price": float(market_data.ask_price) if market_data else None,
                "spread": float(market_data.spread) if market_data and market_data.spread else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch live market", market_id=market_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch market: {str(e)}")


# Demo/Example endpoints (for UI preview without trained models)
@app.get("/demo/predictions", response_model=List[dict])
async def get_demo_predictions(limit: int = Query(default=10, ge=1, le=50)):
    """Get example predictions based on live markets (demo data)."""
    try:
        async with PolymarketDataSource() as polymarket:
            markets = await polymarket.fetch_active_markets(limit=limit)
            
            import random
            demo_predictions = []
            for market in markets[:limit]:
                # Generate mock prediction (model thinks slightly different from market)
                market_prob = float(market.yes_price)
                # Model prediction is market price ± random offset (0-10%)
                offset = random.uniform(-0.10, 0.10)
                model_prob = max(0.01, min(0.99, market_prob + offset))
                edge = model_prob - market_prob
                confidence = random.uniform(0.6, 0.95)  # Mock confidence
                
                demo_predictions.append({
                    "market_id": market.id,
                    "question": market.question,
                    "prediction_time": datetime.now(timezone.utc).isoformat(),
                    "model_probability": round(model_prob, 4),
                    "market_price": round(market_prob, 4),
                    "edge": round(edge, 4),
                    "confidence": round(confidence, 4),
                    "model_version": "demo-v1.0",
                    "model_predictions": {
                        "xgboost": round(model_prob + random.uniform(-0.02, 0.02), 4),
                        "lightgbm": round(model_prob + random.uniform(-0.02, 0.02), 4),
                        "ensemble": round(model_prob, 4),
                    }
                })
            
            return demo_predictions
    except Exception as e:
        logger.error("Failed to generate demo predictions", error=str(e))
        return []


@app.get("/demo/signals", response_model=List[dict])
async def get_demo_signals(limit: int = Query(default=10, ge=1, le=50)):
    """Get example trading signals based on live markets (demo data)."""
    try:
        async with PolymarketDataSource() as polymarket:
            markets = await polymarket.fetch_active_markets(limit=limit * 2)  # Get more to filter
            
            import random
            demo_signals = []
            for market in markets:
                market_prob = float(market.yes_price)
                # Only generate signals where there's a meaningful edge
                model_prob = market_prob + random.uniform(-0.15, 0.15)
                edge = model_prob - market_prob
                abs_edge = abs(edge)
                
                # Only show signals with edge > 5%
                if abs_edge < 0.05:
                    continue
                
                if len(demo_signals) >= limit:
                    break
                
                side = "YES" if edge > 0 else "NO"
                if abs_edge > 0.15:
                    strength = "STRONG"
                elif abs_edge > 0.10:
                    strength = "MEDIUM"
                else:
                    strength = "WEAK"
                
                confidence = random.uniform(0.65, 0.95)
                suggested_size = random.uniform(10, 100)  # Mock position size
                
                demo_signals.append({
                    "market_id": market.id,
                    "question": market.question,
                    "side": side,
                    "signal_strength": strength,
                    "model_probability": round(model_prob, 4),
                    "market_probability": round(market_prob, 4),
                    "edge": round(edge, 4),
                    "confidence": round(confidence, 4),
                    "suggested_size": round(suggested_size, 2),
                    "executed": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            
            return demo_signals[:limit]
    except Exception as e:
        logger.error("Failed to generate demo signals", error=str(e))
        return []


@app.get("/demo/trades", response_model=List[dict])
async def get_demo_trades(limit: int = Query(default=10, ge=1, le=50)):
    """Get example trades (demo data showing what executed trades look like)."""
    try:
        async with PolymarketDataSource() as polymarket:
            markets = await polymarket.fetch_active_markets(limit=limit)
            
            import random
            from datetime import timedelta
            
            demo_trades = []
            for i, market in enumerate(markets):
                market_prob = float(market.yes_price)
                side = random.choice(["YES", "NO"])
                entry_price = market_prob + random.uniform(-0.02, 0.02)
                entry_price = max(0.01, min(0.99, entry_price))
                
                # Some trades are closed, some are open
                is_closed = random.random() > 0.3
                if is_closed:
                    exit_price = entry_price + random.uniform(-0.10, 0.10)
                    exit_price = max(0.01, min(0.99, exit_price))
                    pnl = (exit_price - entry_price) * 100 if side == "YES" else (entry_price - exit_price) * 100
                    status = "CLOSED"
                    exit_time = (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat()
                else:
                    exit_price = None
                    pnl = None
                    status = "OPEN"
                    exit_time = None
                
                size = random.uniform(50, 500)
                entry_time = (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat()
                
                demo_trades.append({
                    "market_id": market.id,
                    "question": market.question,
                    "side": side,
                    "entry_price": round(entry_price, 4),
                    "exit_price": round(exit_price, 4) if exit_price else None,
                    "size": round(size, 2),
                    "pnl": round(pnl, 2) if pnl else None,
                    "status": status,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                })
            
            return demo_trades
    except Exception as e:
        logger.error("Failed to generate demo trades", error=str(e))
        return []


@app.get("/demo/portfolio", response_model=dict)
async def get_demo_portfolio():
    """Get example portfolio snapshot (demo data showing what portfolio tracking looks like)."""
    try:
        import random
        from datetime import timedelta
        
        # Generate realistic portfolio values
        initial_capital = 10000.0
        cash = random.uniform(3000, 7000)  # Some cash remaining
        positions_value = random.uniform(2000, 5000)  # Value in open positions
        total_exposure = positions_value + random.uniform(-500, 500)  # Slight variation
        
        # Generate P&L values
        daily_pnl = random.uniform(-200, 300)  # Can be positive or negative
        unrealized_pnl = random.uniform(-150, 250)  # From open positions
        realized_pnl = random.uniform(100, 500)  # From closed trades (usually positive)
        
        # Total value = cash + positions + unrealized P&L
        total_value = cash + positions_value + unrealized_pnl
        
        return {
            "snapshot_time": datetime.now(timezone.utc).isoformat(),
            "total_value": round(total_value, 2),
            "cash": round(cash, 2),
            "positions_value": round(positions_value, 2),
            "total_exposure": round(total_exposure, 2),
            "daily_pnl": round(daily_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "realized_pnl": round(realized_pnl, 2),
        }
    except Exception as e:
        logger.error("Failed to generate demo portfolio", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate demo portfolio: {str(e)}")


@app.get("/ai/analyze/{market_id}", response_model=dict)
async def analyze_market_ai(market_id: str):
    """AI-powered market analysis."""
    try:
        async with PolymarketDataSource() as polymarket:
            market = await polymarket.fetch_market(market_id)
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            
            market_data = await polymarket.fetch_market_data(market_id)
            
            # Generate AI analysis
            yes_price = float(market.yes_price)
            no_price = float(market.no_price)
            spread = abs(yes_price - no_price) if yes_price and no_price else None
            
            # Analyze market characteristics
            analysis = {
                "market_id": market.id,
                "question": market.question,
                "category": market.category,
                "current_prices": {
                    "yes": round(yes_price, 4),
                    "no": round(no_price, 4),
                    "spread": round(spread, 4) if spread else None,
                },
                "market_analysis": {
                    "liquidity": "High" if market.volume_24h > 10000 else "Medium" if market.volume_24h > 1000 else "Low",
                    "volatility": "High" if spread and spread > 0.1 else "Medium" if spread and spread > 0.05 else "Low",
                    "market_sentiment": "Bullish" if yes_price > 0.6 else "Bearish" if yes_price < 0.4 else "Neutral",
                },
                "ai_insights": [
                    f"Market shows {'strong' if abs(yes_price - 0.5) > 0.2 else 'moderate' if abs(yes_price - 0.5) > 0.1 else 'weak'} directional bias",
                    f"Current pricing suggests {yes_price * 100:.1f}% probability of YES outcome",
                    f"{'High' if market.volume_24h > 10000 else 'Moderate' if market.volume_24h > 1000 else 'Low'} trading volume indicates {'strong' if market.volume_24h > 10000 else 'moderate'} market interest",
                    f"Price spread of {spread * 100:.2f}% suggests {'tight' if spread < 0.05 else 'moderate' if spread < 0.1 else 'wide'} market efficiency" if spread else "Spread data unavailable",
                ],
                "risk_assessment": {
                    "risk_level": "High" if spread and spread > 0.15 else "Medium" if spread and spread > 0.08 else "Low",
                    "recommendation": "Consider position sizing based on spread and liquidity" if spread and spread > 0.1 else "Market appears efficient, smaller edge expected",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to analyze market", market_id=market_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze market: {str(e)}")


@app.get("/ai/analyze-top", response_model=List[dict])
async def analyze_top_markets(limit: int = Query(default=5, ge=1, le=20)):
    """AI analysis for top active markets."""
    try:
        async with PolymarketDataSource() as polymarket:
            markets = await polymarket.fetch_active_markets(limit=limit)
            
            analyses = []
            for market in markets:
                yes_price = float(market.yes_price)
                no_price = float(market.no_price)
                spread = abs(yes_price - no_price) if yes_price and no_price else None
                
                analyses.append({
                    "market_id": market.id,
                    "question": market.question,
                    "category": market.category,
                    "yes_price": round(yes_price, 4),
                    "no_price": round(no_price, 4),
                    "spread": round(spread, 4) if spread else None,
                    "volume_24h": market.volume_24h,
                    "sentiment": "Bullish" if yes_price > 0.6 else "Bearish" if yes_price < 0.4 else "Neutral",
                    "liquidity": "High" if market.volume_24h > 10000 else "Medium" if market.volume_24h > 1000 else "Low",
                    "opportunity_score": round(abs(yes_price - 0.5) * 100, 2),  # Higher = more opportunity
                })
            
            # Sort by opportunity score (highest first)
            analyses.sort(key=lambda x: x["opportunity_score"], reverse=True)
            
            return analyses
    except Exception as e:
        logger.error("Failed to analyze top markets", error=str(e))
        return []


if __name__ == "__main__":
    import uvicorn

    configure_logging()
    uvicorn.run(app, host="0.0.0.0", port=8001)

