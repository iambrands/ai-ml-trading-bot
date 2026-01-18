#!/usr/bin/env python3
"""
Verify indexes are being used and fix if not.
This script:
1. Checks if indexes exist
2. Runs ANALYZE to update statistics
3. Tests if queries use indexes
4. Shows query plans
"""

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
        logger.info("Set it with: export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    logger.info("🔍 Checking index usage...")
    logger.info("")
    
    # Force PostgreSQL to update statistics
    logger.info("📊 Running ANALYZE on all tables...")
    tables = ['portfolio_snapshots', 'markets', 'predictions', 'signals', 'trades']
    for table in tables:
        try:
            cursor.execute(f"ANALYZE {table}")
            logger.info(f"  ✅ ANALYZE {table}")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not ANALYZE {table}: {e}")
    
    conn.commit()
    logger.info("✅ ANALYZE complete")
    logger.info("")
    
    # Check if indexes exist
    logger.info("🔍 Checking indexes on portfolio_snapshots...")
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'portfolio_snapshots'
        ORDER BY indexname
    """)
    indexes = cursor.fetchall()
    logger.info(f"Found {len(indexes)} indexes:")
    for idx_name, idx_def in indexes:
        logger.info(f"  ✅ {idx_name}")
        logger.info(f"     {idx_def[:100]}...")
    logger.info("")
    
    # Test query plan for dashboard stats query
    logger.info("🧪 Testing dashboard stats query plan...")
    logger.info("Query: SELECT ... WHERE paper_trading=true ORDER BY snapshot_time DESC LIMIT 1")
    logger.info("")
    
    try:
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
            SELECT id, snapshot_time, total_value, daily_pnl, unrealized_pnl
            FROM portfolio_snapshots
            WHERE paper_trading = true 
            AND snapshot_time < NOW()
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)
        
        plan = cursor.fetchall()
        plan_text = '\n'.join([row[0] for row in plan])
        
        logger.info("Query Execution Plan:")
        logger.info("-" * 60)
        for line in plan_text.split('\n'):
            logger.info(line)
        logger.info("-" * 60)
        logger.info("")
        
        # Check if using index scan
        if 'Index Scan' in plan_text or 'Index Only Scan' in plan_text:
            logger.info("✅ Query IS using index scan (GOOD!)")
        elif 'Seq Scan' in plan_text:
            logger.warning("⚠️  Query is using sequential scan (NOT using index)")
            logger.warning("  This could be because:")
            logger.warning("    - Table is very small (< 100 rows)")
            logger.warning("    - Query planner thinks sequential scan is faster")
            logger.warning("    - Statistics are stale (should be fixed by ANALYZE above)")
        else:
            logger.info("ℹ️  Could not determine scan type from plan")
        
        # Extract execution time
        for line in plan_text.split('\n'):
            if 'Execution Time' in line:
                logger.info(f"  {line.strip()}")
        
    except Exception as e:
        logger.error(f"❌ Failed to test query plan: {e}")
    
    logger.info("")
    
    # Test markets query plan
    logger.info("🧪 Testing markets query plan...")
    logger.info("Query: SELECT ... WHERE resolution_date >= cutoff ORDER BY created_at DESC LIMIT 100")
    logger.info("")
    
    try:
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM markets
            WHERE (resolution_date IS NULL OR resolution_date >= NOW() - INTERVAL '30 days')
            ORDER BY created_at DESC
            LIMIT 100
        """)
        
        plan = cursor.fetchall()
        plan_text = '\n'.join([row[0] for row in plan])
        
        if 'Index Scan' in plan_text or 'Index Only Scan' in plan_text:
            logger.info("✅ Markets query IS using index scan (GOOD!)")
        elif 'Seq Scan' in plan_text:
            logger.warning("⚠️  Markets query is using sequential scan")
        
        for line in plan_text.split('\n'):
            if 'Execution Time' in line:
                logger.info(f"  {line.strip()}")
        
    except Exception as e:
        logger.error(f"❌ Failed to test markets query plan: {e}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Index verification complete")
    logger.info("=" * 60)
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()

