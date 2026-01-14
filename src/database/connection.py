"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Create async engine with error handling (database is optional)
engine = None
AsyncSessionLocal = None

try:
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using
        pool_size=20,  # Increased from 10 - base pool size for better performance
        max_overflow=30,  # Increased from 20 - allow more connections during spikes
        pool_recycle=1800,  # Recycle connections every 30 min (reduced from 1 hour for better connection health)
        pool_timeout=30,  # Max wait time for connection
        connect_args={
            "command_timeout": 30,  # 30 second query timeout
            "server_settings": {
                "statement_timeout": "30000",  # 30 second statement timeout
            }
        },
    )
    
    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.warning("Database not available (this is OK - API will work without DB)", error=str(e))
    engine = None
    AsyncSessionLocal = None

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    if not AsyncSessionLocal:
        raise Exception("Database not configured")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    if not engine:
        logger.warning("Database engine not available, skipping initialization")
        return
    
    try:
        async with engine.begin() as conn:
            # Import all models to register them
            from . import models  # noqa: F401
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning("Database initialization failed (this is OK if DB is not set up)", error=str(e))


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()


def get_pool_stats():
    """Get connection pool statistics for monitoring."""
    if not engine:
        return None
    
    try:
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
            "utilization": pool.checkedout() / pool.size() if pool.size() > 0 else 0,
        }
    except Exception as e:
        logger.warning("Failed to get pool stats", error=str(e))
        return None

