#!/usr/bin/env python3
"""
Diagnostic Script for PredictEdge Features
Identifies issues with whale tracker and economic calendar.
"""

import os
import sys
import psycopg2
import requests
from pathlib import Path
from datetime import datetime

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}  {title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_check(status, message):
    icon = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    print(f"{icon} {message}")

def print_warning(message):
    print(f"{YELLOW}⚠{RESET}  {message}")

def print_info(message):
    print(f"{BLUE}ℹ{RESET}  {message}")

# ============================================================================
# DATABASE DIAGNOSTICS
# ============================================================================

def check_database_connection(db_url):
    """Check if database is accessible"""
    print_header("DATABASE CONNECTION CHECK")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print_check(True, "Database connection successful")
        print_info(f"PostgreSQL: {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print_check(False, f"Database connection failed: {e}")
        return False

def check_tables_exist(db_url):
    """Check if required tables exist"""
    print_header("TABLE EXISTENCE CHECK")
    
    required_tables = [
        'whale_wallets',
        'whale_trades', 
        'whale_alerts',
        'economic_events',
        'market_events',
        'event_alerts'
    ]
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        all_exist = True
        for table in required_tables:
            exists = table in existing_tables
            print_check(exists, f"Table '{table}' exists")
            if not exists:
                all_exist = False
        
        cursor.close()
        conn.close()
        
        if not all_exist:
            print_warning("Some tables are missing. Run migrations:")
            print_info("  railway run psql $DATABASE_URL -f src/database/migrations/004_whale_tracking.sql")
            print_info("  railway run psql $DATABASE_URL -f src/database/migrations/005_economic_calendar.sql")
        
        return all_exist
    except Exception as e:
        print_check(False, f"Table check failed: {e}")
        return False

def check_data_exists(db_url):
    """Check if tables have data"""
    print_header("DATA EXISTENCE CHECK")
    
    queries = [
        ("Whale Wallets", "SELECT COUNT(*) FROM whale_wallets WHERE is_active = true"),
        ("Whale Trades", "SELECT COUNT(*) FROM whale_trades WHERE trade_time > NOW() - INTERVAL '7 days'"),
        ("Whale Alerts", "SELECT COUNT(*) FROM whale_alerts WHERE is_read = false"),
        ("Economic Events", "SELECT COUNT(*) FROM economic_events WHERE event_date > NOW()"),
        ("Market Events", "SELECT COUNT(*) FROM market_events"),
    ]
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        has_data = {}
        for name, query in queries:
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                has_data[name] = count
                
                if count > 0:
                    print_check(True, f"{name}: {count} records")
                else:
                    print_check(False, f"{name}: NO DATA")
            except Exception as e:
                print_check(False, f"{name}: Query failed - {e}")
                has_data[name] = 0
        
        cursor.close()
        conn.close()
        
        # Recommendations
        if has_data.get("Economic Events", 0) == 0:
            print_warning("No economic events found. Initialize calendar:")
            print_info("  railway run python scripts/init_economic_calendar.py")
        
        if has_data.get("Whale Wallets", 0) == 0:
            print_warning("No whales found. Run discovery:")
            print_info("  railway run python scripts/init_whale_discovery.py")
        
        return sum(has_data.values()) > 0
    except Exception as e:
        print_check(False, f"Data check failed: {e}")
        return False

def check_indexes(db_url):
    """Check if indexes exist"""
    print_header("INDEX CHECK")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND (indexname LIKE 'idx_whale%' OR indexname LIKE 'idx_economic%' OR indexname LIKE 'idx_market_events%')
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print_check(True, f"Found {len(indexes)} indexes")
            for idx_name, table_name in indexes[:10]:
                print_info(f"  {table_name}.{idx_name}")
            if len(indexes) > 10:
                print_info(f"  ... and {len(indexes) - 10} more")
        else:
            print_check(False, "No indexes found")
        
        cursor.close()
        conn.close()
        
        return len(indexes) > 0
    except Exception as e:
        print_check(False, f"Index check failed: {e}")
        return False

# ============================================================================
# API ENDPOINT DIAGNOSTICS
# ============================================================================

def check_api_endpoints(base_url):
    """Test all API endpoints"""
    print_header("API ENDPOINT CHECK")
    
    endpoints = [
        ("GET", "/health", "Health check"),
        ("GET", "/whales/leaderboard?limit=5", "Whale leaderboard"),
        ("GET", "/whales/recent-activity?hours=24", "Whale activity"),
        ("GET", "/api/calendar/upcoming?days=30", "Calendar upcoming"),
        ("GET", "/api/calendar/stats", "Calendar stats"),
    ]
    
    results = {}
    for method, path, description in endpoints:
        url = f"{base_url}{path}"
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                print_check(True, f"{description}: {status}")
                try:
                    data = response.json()
                    # Show some data info
                    if isinstance(data, list):
                        print_info(f"  → {len(data)} items returned")
                    elif isinstance(data, dict):
                        if 'whales' in data:
                            print_info(f"  → {len(data['whales'])} whales returned")
                        elif 'events' in data:
                            print_info(f"  → {len(data['events'])} events returned")
                        elif 'trades' in data:
                            print_info(f"  → {len(data['trades'])} trades returned")
                        elif 'count' in data:
                            print_info(f"  → Count: {data.get('count', 0)}")
                except:
                    pass
                results[path] = True
            else:
                print_check(False, f"{description}: {status}")
                try:
                    error_text = response.text[:200]
                    print_warning(f"  Response: {error_text}")
                except:
                    pass
                results[path] = False
        except requests.exceptions.Timeout:
            print_check(False, f"{description}: TIMEOUT")
            results[path] = False
        except Exception as e:
            print_check(False, f"{description}: {e}")
            results[path] = False
    
    return all(results.values())

def check_frontend_paths(base_url):
    """Check if frontend is calling correct API paths"""
    print_header("FRONTEND API PATH CHECK")
    
    try:
        # Fetch index.html
        response = requests.get(base_url, timeout=10)
        html = response.text
        
        # Check for wrong paths
        wrong_paths = [
            "'/calendar/upcoming'",
            '"/calendar/upcoming"',
            "'/calendar/event/",
            '"/calendar/event/',
        ]
        
        correct_paths = [
            "'/api/calendar/upcoming'",
            '"/api/calendar/upcoming"',
            "'/api/calendar/event/",
            '"/api/calendar/event/',
        ]
        
        issues_found = []
        for wrong in wrong_paths:
            if wrong in html:
                issues_found.append(wrong)
        
        if issues_found:
            print_check(False, "Frontend using incorrect API paths")
            for issue in issues_found:
                print_warning(f"  Found: {issue}")
            print_info("  Should use: /api/calendar/* instead of /calendar/*")
            print_info("  Fix in: src/api/static/index.html")
        else:
            print_check(True, "Frontend API paths look correct")
        
        return len(issues_found) == 0
    except Exception as e:
        print_check(False, f"Frontend check failed: {e}")
        return False

# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

def check_environment():
    """Check required environment variables"""
    print_header("ENVIRONMENT VARIABLES CHECK")
    
    required_vars = {
        'DATABASE_URL': 'Database connection',
        'ALCHEMY_API_KEY': 'Whale tracking (Alchemy API)',
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print_check(True, f"{var}: {masked} ({description})")
        else:
            print_check(False, f"{var}: NOT SET ({description})")
            all_set = False
    
    if not all_set:
        print_warning("Set missing variables in Railway dashboard")
    
    return all_set

# ============================================================================
# MAIN DIAGNOSTIC FLOW
# ============================================================================

def main():
    """Run all diagnostics"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}  PREDICTEDGE DIAGNOSTIC TOOL{RESET}")
    print(f"{BLUE}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    # Get configuration
    db_url = os.getenv('DATABASE_URL')
    base_url = os.getenv('API_BASE_URL', 'https://web-production-c490dd.up.railway.app')
    
    if not db_url:
        print(f"\n{RED}ERROR: DATABASE_URL not set{RESET}")
        print("Set it with: export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    print(f"\n{BLUE}Configuration:{RESET}")
    print(f"  API URL: {base_url}")
    print(f"  Database: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    
    # Run all checks
    results = {}
    
    results['env'] = check_environment()
    results['db_connection'] = check_database_connection(db_url)
    
    if results['db_connection']:
        results['tables'] = check_tables_exist(db_url)
        results['indexes'] = check_indexes(db_url)
        results['data'] = check_data_exists(db_url)
    
    results['api'] = check_api_endpoints(base_url)
    results['frontend'] = check_frontend_paths(base_url)
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nChecks Passed: {passed}/{total}\n")
    
    if passed == total:
        print(f"{GREEN}✓ All checks passed! System is healthy.{RESET}\n")
    else:
        print(f"{YELLOW}⚠ Issues detected. Follow recommendations above.{RESET}\n")
        
        # Priority recommendations
        print(f"{BLUE}Priority Actions:{RESET}")
        
        if not results.get('tables'):
            print(f"  {RED}1. RUN MIGRATIONS{RESET}")
            print("     railway run psql $DATABASE_URL -f src/database/migrations/004_whale_tracking.sql")
            print("     railway run psql $DATABASE_URL -f src/database/migrations/005_economic_calendar.sql")
        
        if not results.get('data'):
            print(f"  {RED}2. INITIALIZE DATA{RESET}")
            print("     railway run python scripts/init_economic_calendar.py")
            print("     railway run python scripts/init_whale_discovery.py")
        
        if not results.get('frontend'):
            print(f"  {RED}3. FIX FRONTEND PATHS{RESET}")
            print("     Update src/api/static/index.html")
            print("     Change /calendar/* to /api/calendar/*")
        
        if not results.get('api'):
            print(f"  {RED}4. CHECK API LOGS{RESET}")
            print("     railway logs --tail 100")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Diagnostic interrupted by user{RESET}\n")
    except Exception as e:
        print(f"\n\n{RED}Diagnostic failed: {e}{RESET}\n")
        import traceback
        traceback.print_exc()

