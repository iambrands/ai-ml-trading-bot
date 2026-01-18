#!/usr/bin/env python3
"""
Economic Calendar Initialization Script

This script:
1. Runs the database migration (005_economic_calendar.sql)
2. Initializes the 2026 economic calendar with FOMC, CPI, NFP, GDP events
3. Matches markets to events using keyword analysis

Usage:
    python scripts/init_economic_calendar.py
    
Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string from Railway
"""

import os
import sys
import asyncio
import psycopg2
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import AsyncSessionLocal
from src.services.economic_calendar import EconomicCalendar
from src.utils.logging import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


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


def read_migration_file():
    """Read the migration SQL file"""
    migration_path = project_root / "src" / "database" / "migrations" / "005_economic_calendar.sql"
    
    if not migration_path.exists():
        logger.error(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)
    
    logger.info(f"📄 Reading migration file: {migration_path.name}")
    with open(migration_path, 'r') as f:
        return f.read()


def run_migration(conn, migration_sql):
    """Run the SQL migration"""
    logger.info("🚀 Running database migration...")
    
    cursor = conn.cursor()
    
    try:
        # Execute migration SQL
        cursor.execute(migration_sql)
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('economic_events', 'market_events', 'event_alerts', 'event_market_impact')
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['economic_events', 'event_alerts', 'event_market_impact', 'market_events']
        missing = [t for t in expected_tables if t not in tables]
        
        if missing:
            logger.error(f"❌ Missing tables after migration: {missing}")
            return False
        
        logger.info(f"✅ Migration completed - {len(tables)} tables created:")
        for table in tables:
            logger.info(f"   - {table}")
        
        # Verify indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('economic_events', 'market_events', 'event_alerts', 'event_market_impact')
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        logger.info(f"✅ Created {len(indexes)} indexes")
        
        conn.commit()
        logger.info("✅ Migration committed to database")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()


async def initialize_calendar():
    """Initialize the economic calendar with 2026 events"""
    logger.info("📅 Initializing economic calendar...")
    
    try:
        async with AsyncSessionLocal() as db:
            calendar = EconomicCalendar(db)
            
            # Initialize events
            logger.info("   Creating 2026 events...")
            event_count = await calendar.initialize_2026_calendar()
            logger.info(f"   ✅ Created {event_count} events")
            
            # Match markets to events
            logger.info("   Matching markets to events...")
            match_count = await calendar.match_markets_to_events()
            logger.info(f"   ✅ Matched {match_count} market-event relationships")
            
            return event_count, match_count
            
    except Exception as e:
        logger.error(f"❌ Calendar initialization failed: {e}", exc_info=True)
        raise


def verify_initialization(conn):
    """Verify calendar was initialized correctly"""
    logger.info("🔍 Verifying initialization...")
    
    cursor = conn.cursor()
    
    try:
        # Count events by type
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM economic_events
            GROUP BY event_type
            ORDER BY event_type
        """)
        
        type_counts = cursor.fetchall()
        
        logger.info("   Event counts by type:")
        total_events = 0
        for event_type, count in type_counts:
            logger.info(f"   - {event_type}: {count}")
            total_events += count
        
        logger.info(f"   Total events: {total_events}")
        
        # Count upcoming events
        cursor.execute("""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE event_date > NOW()
            AND is_completed = false
        """)
        
        upcoming_count = cursor.fetchone()[0]
        logger.info(f"   Upcoming events: {upcoming_count}")
        
        # Count market-event relationships
        cursor.execute("SELECT COUNT(*) FROM market_events")
        relationship_count = cursor.fetchone()[0]
        logger.info(f"   Market-event relationships: {relationship_count}")
        
        return total_events > 0
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()


def main():
    """Main script entry point"""
    logger.info("=" * 70)
    logger.info("  ECONOMIC CALENDAR INITIALIZATION")
    logger.info("  Running migration and initializing 2026 events")
    logger.info("=" * 70)
    logger.info("")
    
    # Step 1: Run migration
    logger.info("STEP 1: Running Database Migration")
    logger.info("-" * 70)
    
    db_url = get_database_url()
    conn = connect_to_database(db_url)
    
    try:
        migration_sql = read_migration_file()
        migration_success = run_migration(conn, migration_sql)
        
        if not migration_success:
            logger.error("❌ Migration failed - aborting")
            sys.exit(1)
        
        logger.info("")
        
        # Step 2: Initialize calendar
        logger.info("STEP 2: Initializing Economic Calendar")
        logger.info("-" * 70)
        
        event_count, match_count = asyncio.run(initialize_calendar())
        
        logger.info("")
        
        # Step 3: Verify
        logger.info("STEP 3: Verification")
        logger.info("-" * 70)
        
        verified = verify_initialization(conn)
        
        if not verified:
            logger.error("❌ Verification failed")
            sys.exit(1)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("  ✅ INITIALIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  • Events created: {event_count}")
        logger.info(f"  • Market-event relationships: {match_count}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Visit the Economic Calendar tab in PredictEdge")
        logger.info("  2. Filter events by type (FOMC, CPI, NFP, GDP)")
        logger.info("  3. Click events to see related markets")
        logger.info("")
        logger.info("API Endpoints:")
        logger.info("  GET /calendar/upcoming - List upcoming events")
        logger.info("  GET /calendar/event/{id}/markets - Get event markets")
        logger.info("  GET /calendar/stats - Get calendar statistics")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}", exc_info=True)
        conn.rollback()
        logger.error("Rolled back all changes")
        sys.exit(1)
        
    finally:
        conn.close()
        logger.info("🔌 Database connection closed")


if __name__ == "__main__":
    main()

