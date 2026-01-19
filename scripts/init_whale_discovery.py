#!/usr/bin/env python3
"""
Whale Discovery Initialization Script

This script:
1. Discovers top 500 whales from Polymarket subgraph
2. Indexes whales in the database
3. Optionally monitors recent trades

Usage:
    python scripts/init_whale_discovery.py
    
Environment Variables:
    DATABASE_URL - PostgreSQL connection string (required)
    ALCHEMY_API_KEY - Alchemy API key (optional, for future Web3 integration)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import AsyncSessionLocal
from src.services.whale_tracker import WhaleTracker
from src.utils.logging import get_logger

logger = get_logger(__name__)

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_check(status, message):
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")

async def discover_and_index_whales():
    """Discover whales and index them"""
    print_header("WHALE DISCOVERY INITIALIZATION")
    
    try:
        # Check database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not found in environment")
            print("   Please set DATABASE_URL to enable whale discovery")
            print("\n   Run: railway variables | grep DATABASE_URL")
            return False
        
        print_check(True, f"Database URL configured")
        
        # Check Alchemy key (optional for now, used for future Web3 integration)
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        if alchemy_key:
            print_check(True, f"Alchemy API key found: {alchemy_key[:10]}...")
        else:
            print_check(False, "ALCHEMY_API_KEY not set (optional, for future Web3 integration)")
            print("   Note: WhaleTracker uses Polymarket subgraph, not Alchemy")
        
        print("\n" + "-"*70)
        print("STEP 1: Discovering Top Whales")
        print("-"*70)
        
        # Create database session
        async with AsyncSessionLocal() as db:
            tracker = WhaleTracker(db, alchemy_api_key=alchemy_key)
            
            print("🐋 Connecting to Polymarket APIs...")
            print("   Using Gamma API for market data")
            print("   Using CLOB API for order books")
            print("   This may take 30-60 seconds...\n")
            
            # Discover whales
            whales = await tracker.discover_whales()
            
            if not whales:
                print("⚠️  No whales discovered - subgraph may be unavailable")
                print("   Try again in a few minutes")
                await tracker.close()
                return False
            
            print_check(True, f"Discovered {len(whales)} whale wallets\n")
            
            print("-"*70)
            print("STEP 2: Indexing Whales in Database")
            print("-"*70)
            
            # Index whales
            print("💾 Indexing whales in database...")
            indexed = await tracker.index_whales(whales)
            print_check(True, f"Indexed {indexed} whales\n")
            
            await tracker.close()
        
        print_header("INITIALIZATION COMPLETED SUCCESSFULLY")
        
        print(f"✅ Discovered: {len(whales)} whales")
        print(f"✅ Indexed: {indexed} whales")
        print("\nNext steps:")
        print("1. Check whale leaderboard: curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=10")
        print("2. View in UI: Navigate to '🐋 Whale Tracker' tab in dashboard")
        print("3. Run diagnostics: railway run python scripts/diagnose_issues.py")
        
        return True
        
    except Exception as e:
        logger.error(f"Whale discovery failed: {e}", exc_info=True)
        print(f"\n❌ Whale discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point"""
    success = await discover_and_index_whales()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

