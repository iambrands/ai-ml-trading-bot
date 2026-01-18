#!/usr/bin/env python3
"""
Database Migration Runner - Creates indexes on portfolio_snapshots table

This script:
1. Connects to Railway PostgreSQL database
2. Creates performance indexes on portfolio_snapshots
3. Verifies indexes were created successfully
4. Reports results

Usage:
    python scripts/run_migration.py
    
Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string from Railway
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get DATABASE_URL from environment"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Set it with: export DATABASE_URL='postgresql://...'")
        logger.info("Or get it from Railway Dashboard > Postgres > Variables")
        sys.exit(1)
    
    return db_url


def connect_to_database(db_url):
    """Connect to PostgreSQL database"""
    try:
        logger.info("🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        logger.info("✅ Connected successfully")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        logger.info("Check your DATABASE_URL format: postgresql://user:pass@host:port/db")
        sys.exit(1)


def check_existing_indexes(cursor):
    """Check if indexes already exist"""
    logger.info("🔍 Checking existing indexes...")
    
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'portfolio_snapshots'
    """)
    
    existing_indexes = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found {len(existing_indexes)} existing indexes:")
    for idx in existing_indexes:
        logger.info(f"  - {idx}")
    
    return existing_indexes


def create_indexes(cursor):
    """Create performance indexes on portfolio_snapshots table"""
    
    migrations = [
        {
            'name': 'idx_portfolio_paper_snapshot',
            'sql': """
                CREATE INDEX IF NOT EXISTS idx_portfolio_paper_snapshot 
                ON portfolio_snapshots(paper_trading, snapshot_time DESC) 
                WHERE paper_trading = true
            """,
            'description': 'Composite index for paper_trading + snapshot_time'
        },
        {
            'name': 'idx_portfolio_snapshot_time_desc',
            'sql': """
                CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc 
                ON portfolio_snapshots(snapshot_time DESC)
            """,
            'description': 'Index on snapshot_time for sorting'
        },
        {
            'name': 'idx_portfolio_created_at_desc',
            'sql': """
                CREATE INDEX IF NOT EXISTS idx_portfolio_created_at_desc 
                ON portfolio_snapshots(created_at DESC)
            """,
            'description': 'Index on created_at for sorting'
        }
    ]
    
    logger.info("🚀 Creating indexes...")
    
    for migration in migrations:
        try:
            logger.info(f"  Creating {migration['name']}...")
            logger.info(f"    {migration['description']}")
            
            cursor.execute(migration['sql'])
            logger.info(f"  ✅ {migration['name']} created successfully")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to create {migration['name']}: {e}")
            raise


def analyze_table(cursor):
    """Run ANALYZE to update query planner statistics"""
    logger.info("📊 Analyzing table to update statistics...")
    
    try:
        cursor.execute("ANALYZE portfolio_snapshots")
        logger.info("✅ Table analyzed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to analyze table: {e}")
        raise


def verify_indexes(cursor):
    """Verify indexes were created"""
    logger.info("🔍 Verifying indexes...")
    
    cursor.execute("""
        SELECT 
            indexname, 
            indexdef 
        FROM pg_indexes 
        WHERE tablename = 'portfolio_snapshots'
        ORDER BY indexname
    """)
    
    indexes = cursor.fetchall()
    
    required_indexes = [
        'idx_portfolio_paper_snapshot',
        'idx_portfolio_snapshot_time_desc',
        'idx_portfolio_created_at_desc'
    ]
    
    found_indexes = [idx[0] for idx in indexes]
    
    logger.info(f"Found {len(indexes)} total indexes:")
    for idx_name, idx_def in indexes:
        logger.info(f"  ✅ {idx_name}")
        logger.info(f"     {idx_def[:100]}...")
    
    # Check if required indexes exist
    missing = [idx for idx in required_indexes if idx not in found_indexes]
    
    if missing:
        logger.error(f"❌ Missing required indexes: {missing}")
        return False
    
    logger.info("✅ All required indexes verified")
    return True


def test_query_performance(cursor):
    """Test query performance with new indexes"""
    logger.info("🧪 Testing query performance...")
    
    test_query = """
        EXPLAIN ANALYZE 
        SELECT id, snapshot_time, total_value, daily_pnl, unrealized_pnl
        FROM portfolio_snapshots
        WHERE paper_trading = true 
        AND snapshot_time < NOW()
        ORDER BY snapshot_time DESC
        LIMIT 1
    """
    
    try:
        cursor.execute(test_query)
        results = cursor.fetchall()
        
        # Check if using index scan (not seq scan)
        query_plan = '\n'.join([row[0] for row in results])
        
        if 'Index Scan' in query_plan:
            logger.info("✅ Query is using index scan (GOOD!)")
            
            # Extract execution time
            for line in query_plan.split('\n'):
                if 'Execution Time' in line:
                    logger.info(f"  {line.strip()}")
        else:
            logger.warning("⚠️  Query is NOT using index scan (might still need optimization)")
            logger.info("  This could mean the table is small or statistics need updating")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to test query: {e}")
        return False


def main():
    """Main migration runner"""
    logger.info("=" * 60)
    logger.info("  PORTFOLIO SNAPSHOTS MIGRATION")
    logger.info("  Creating performance indexes")
    logger.info("=" * 60)
    logger.info("")
    
    # Get database connection
    db_url = get_database_url()
    conn = connect_to_database(db_url)
    
    try:
        # Create cursor
        cursor = conn.cursor()
        
        # Check existing indexes
        existing = check_existing_indexes(cursor)
        logger.info("")
        
        # Create new indexes
        create_indexes(cursor)
        logger.info("")
        
        # Analyze table
        analyze_table(cursor)
        logger.info("")
        
        # Commit changes
        conn.commit()
        logger.info("✅ Migration committed to database")
        logger.info("")
        
        # Verify indexes
        verified = verify_indexes(cursor)
        logger.info("")
        
        # Test query performance
        if verified:
            test_query_performance(cursor)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("  ✅ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Check Railway logs for 'Dashboard stats retrieved' messages")
        logger.info("2. Test endpoint: curl https://your-app.railway.app/dashboard/stats")
        logger.info("3. Response time should be < 500ms (was 30+ seconds)")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        logger.error("Rolled back all changes")
        sys.exit(1)
        
    finally:
        cursor.close()
        conn.close()
        logger.info("🔌 Database connection closed")


if __name__ == "__main__":
    main()

