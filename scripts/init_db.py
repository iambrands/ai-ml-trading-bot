"""Initialize database schema."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def main():
    """Initialize database."""
    configure_logging()
    logger.info("Initializing database schema...")
    
    try:
        await init_db()
        logger.info("✅ Database schema initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())

