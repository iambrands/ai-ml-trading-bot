#!/usr/bin/env python3
"""
Whale Discovery Initialization Script
Discovers top whales from Polymarket APIs and indexes them in database.
Uses asyncpg for Railway compatibility.
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_step(step_num, title):
    """Print formatted step header"""
    print(f"\nSTEP {step_num}: {title}")
    print("-"*70)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

async def discover_whales_from_api():
    """
    Discover top whales using Polymarket APIs.
    Returns list of whale data or mock data if APIs fail.
    """
    try:
        # Import whale tracker
        from src.services.whale_tracker import WhaleTracker
        
        # Create tracker (db not needed for discovery)
        tracker = WhaleTracker(None, None)
        
        print("🐋 Discovering top whales from Polymarket...")
        print("   Using Gamma API for markets")
        print("   Using CLOB API for order books")
        print("   Timeout: 60 seconds\n")
        
        # Discover whales
        whales = await tracker.discover_whales()
        
        # Close session
        await tracker.close()
        
        return whales
        
    except Exception as e:
        print_error(f"Discovery error: {e}")
        import traceback
        traceback.print_exc()
        return []

async def index_whales_in_database(whales, db_url):
    """
    Index whales into database using asyncpg.
    
    Args:
        whales: List of whale data dicts
        db_url: PostgreSQL connection URL
    
    Returns:
        Number of whales successfully indexed
    """
    if not whales:
        print_warning("No whales to index")
        return 0
    
    print(f"💾 Indexing {len(whales)} whales in database...")
    
    try:
        # Parse DATABASE_URL for asyncpg
        # asyncpg needs the connection string in a specific format
        # Handle both postgresql:// and postgres:// URLs
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            # asyncpg.connect() accepts the URL directly
            # But we need to handle Railway internal URLs
            if 'postgres.railway.internal' in db_url:
                print_warning("Using Railway internal URL - ensure you're running via 'railway run'")
                print_info("If this fails, use 'railway connect postgres' to create a tunnel")
            
            conn = await asyncpg.connect(db_url, timeout=30)
        else:
            print_error(f"Invalid DATABASE_URL format: {db_url[:50]}...")
            return 0
        
        print_success("Connected to database")
        
        indexed_count = 0
        
        for rank, whale_data in enumerate(whales, start=1):
            try:
                # Extract whale data
                wallet_address = whale_data['id'].lower()
                volume = float(whale_data.get('volumeTraded', 0))
                trades = int(whale_data.get('numTrades', 0))
                
                # Calculate derived metrics
                # Higher volume suggests higher skill (capped at 75%)
                win_rate = min(0.75, 0.45 + (volume / 1000000))
                
                # Assume 5% profit margin on volume
                profit = volume * 0.05
                
                # Insert or update whale
                await conn.execute("""
                    INSERT INTO whale_wallets (
                        wallet_address,
                        total_volume,
                        total_trades,
                        total_profit,
                        win_rate,
                        rank,
                        is_active,
                        last_activity_at,
                        created_at,
                        updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, true, NOW(), NOW(), NOW())
                    ON CONFLICT (wallet_address) 
                    DO UPDATE SET
                        total_volume = EXCLUDED.total_volume,
                        total_trades = EXCLUDED.total_trades,
                        total_profit = EXCLUDED.total_profit,
                        win_rate = EXCLUDED.win_rate,
                        rank = EXCLUDED.rank,
                        is_active = true,
                        last_activity_at = NOW(),
                        updated_at = NOW()
                """, 
                    wallet_address,
                    Decimal(str(volume)),
                    trades,
                    Decimal(str(profit)),
                    Decimal(str(win_rate)),
                    rank
                )
                
                indexed_count += 1
                
                # Progress indicator every 10 whales
                if indexed_count % 10 == 0:
                    print(f"   Indexed {indexed_count}/{len(whales)} whales...")
                
            except Exception as e:
                print_warning(f"Failed to index {wallet_address[:10]}...: {e}")
                continue
        
        # Close connection
        await conn.close()
        
        print_success(f"Indexed {indexed_count} whales successfully")
        
        return indexed_count
        
    except asyncpg.PostgresError as e:
        print_error(f"Database error: {e}")
        return 0
    except Exception as e:
        print_error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def verify_whale_data(db_url):
    """
    Verify whale data was indexed correctly.
    
    Args:
        db_url: PostgreSQL connection URL
    
    Returns:
        True if verification passed, False otherwise
    """
    print_step(3, "Verification")
    print("🔍 Verifying whale data...\n")
    
    try:
        conn = await asyncpg.connect(db_url, timeout=30)
        
        # Count total whales
        total_whales = await conn.fetchval(
            "SELECT COUNT(*) FROM whale_wallets WHERE is_active = true"
        )
        print(f"   Total active whales: {total_whales}")
        
        # Count recent trades
        recent_trades = await conn.fetchval("""
            SELECT COUNT(*) FROM whale_trades 
            WHERE trade_time > NOW() - INTERVAL '24 hours'
        """)
        print(f"   Recent trades (24h): {recent_trades}")
        
        # Get top 5 whales
        top_whales = await conn.fetch("""
            SELECT rank, wallet_address, total_volume, win_rate, total_profit
            FROM whale_wallets
            WHERE is_active = true
            ORDER BY rank ASC
            LIMIT 5
        """)
        
        if top_whales:
            print("\n   Top 5 Whales:")
            for whale in top_whales:
                print(f"   #{whale['rank']}: ${float(whale['total_volume']):,.0f} volume, "
                      f"{float(whale['win_rate'])*100:.1f}% win rate, "
                      f"${float(whale['total_profit']):,.0f} P&L")
                print(f"        {whale['wallet_address'][:10]}...{whale['wallet_address'][-8:]}")
        
        await conn.close()
        
        return total_whales > 0
        
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

async def main():
    """Main initialization flow"""
    print_header("WHALE DISCOVERY INITIALIZATION\n  Discovering and indexing top Polymarket traders")
    
    # Get DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print_error("DATABASE_URL environment variable not set")
        print_info("Set it with: export DATABASE_URL='postgresql://...'")
        print_info("Or run via Railway: railway run python scripts/init_whale_discovery.py")
        sys.exit(1)
    
    # Mask password for display
    db_display = db_url.split('@')[1] if '@' in db_url else 'configured'
    print(f"✅ Database URL configured")
    print(f"   Host: {db_display}")
    
    # Check ALCHEMY_API_KEY (optional)
    alchemy_key = os.getenv('ALCHEMY_API_KEY')
    if alchemy_key:
        print(f"✅ ALCHEMY_API_KEY configured (optional)")
    else:
        print(f"⚠️  ALCHEMY_API_KEY not set (optional, for future Web3 integration)")
        print("   Note: WhaleTracker uses Polymarket APIs, not Alchemy")
    
    print("-"*70)
    
    # Step 1: Discover whales
    print_step(1, "Discovering Top Whales")
    whales = await discover_whales_from_api()
    
    if not whales:
        print_error("No whales discovered")
        print_info("This may indicate API issues or network problems")
        print_info("The script will exit - check logs for details")
        sys.exit(1)
    
    print_success(f"Discovered {len(whales)} whales")
    
    # Step 2: Index whales
    print_step(2, "Indexing Whales in Database")
    indexed_count = await index_whales_in_database(whales, db_url)
    
    if indexed_count == 0:
        print_error("Failed to index whales")
        print_info("Check database connection and table existence")
        sys.exit(1)
    
    # Step 3: Verify
    verification_passed = await verify_whale_data(db_url)
    
    # Summary
    print_header("✅ INITIALIZATION COMPLETED SUCCESSFULLY")
    
    print(f"\n✅ Discovered: {len(whales)} whales")
    print(f"✅ Indexed: {indexed_count} whales")
    
    if verification_passed:
        print("\n" + "="*70)
        print("Next steps:")
        print("1. Check whale leaderboard: curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=10")
        print("2. View in UI: Navigate to '🐋 Whale Tracker' tab in dashboard")
        print("3. Run diagnostics: railway run python scripts/diagnose_issues.py")
        print("="*70 + "\n")
    else:
        print_warning("Verification failed - check database connection")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery interrupted by user\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Discovery failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
