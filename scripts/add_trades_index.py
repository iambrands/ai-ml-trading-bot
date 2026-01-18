#!/usr/bin/env python3
"""Add index to trades table for active positions query"""

import os
import sys
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    logger.info("🚀 Creating index on trades.status...")
    
    try:
        # Create index on trades.status for active positions query
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_status_created 
            ON trades(status, created_at DESC) 
            WHERE status = 'OPEN'
        """)
        
        # Also create index on paper_trading for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_paper_status 
            ON trades(paper_trading, status, created_at DESC)
        """)
        
        # Analyze table to update statistics
        cursor.execute("ANALYZE trades")
        
        conn.commit()
        
        logger.info("✅ Trades indexes created successfully")
        logger.info("  - idx_trades_status_created (for active positions)")
        logger.info("  - idx_trades_paper_status (for paper trading filter)")
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()

