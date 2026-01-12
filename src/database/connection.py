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
        pool_size=5,  # Reduced for Railway free tier limits
        max_overflow=5,  # Reduced to prevent connection exhaustion
        pool_timeout=30,  # Timeout after 30s if pool is exhausted
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

