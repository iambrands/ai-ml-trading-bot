#!/usr/bin/env python3
"""
Comprehensive database diagnostics.
Identifies why queries are slow despite indexes.
"""

import os
import sys
import psycopg2
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("DATABASE PERFORMANCE DIAGNOSTICS")
    logger.info("=" * 70)
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL not set")
        logger.info("Set it with: export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    logger.info(f"\n🔌 Connecting to database...")
    try:
        host = db_url.split('@')[1].split(':')[0]
        logger.info(f"   Host: {host}")
    except:
        logger.info("   Host: (extracting from URL)")
    
    try:
        start = time.time()
        conn = psycopg2.connect(db_url, connect_timeout=10)
        connect_time = time.time() - start
        logger.info(f"✅ Connected in {connect_time:.3f}s")
        
        cursor = conn.cursor()
        
        # Test 1: Connection latency
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: Network Latency")
        logger.info("=" * 70)
        
        latencies = []
        for i in range(5):
            start = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            latency = time.time() - start
            latencies.append(latency)
            logger.info(f"  Ping {i+1}: {latency*1000:.1f}ms")
        
        avg_latency = sum(latencies) / len(latencies)
        logger.info(f"\n  Average latency: {avg_latency*1000:.1f}ms")
        
        if avg_latency > 0.1:
            logger.warning(f"  ⚠️  High latency detected ({avg_latency*1000:.1f}ms)")
            logger.warning("     This could explain slow queries")
        
        # Test 2: Table sizes and row counts
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Table Sizes")
        logger.info("=" * 70)
        
        tables = ['portfolio_snapshots', 'markets', 'predictions', 'signals', 'trades']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table}'))
                """)
                size = cursor.fetchone()[0]
                
                logger.info(f"  {table:25} {count:>8} rows    {size:>10}")
                
            except Exception as e:
                logger.error(f"  {table:25} ERROR: {e}")
        
        # Test 3: Index status
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: Index Status on portfolio_snapshots")
        logger.info("=" * 70)
        
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 'portfolio_snapshots'
            ORDER BY indexname
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            for schema, table, idx_name, idx_def in indexes:
                logger.info(f"\n  ✅ {idx_name}")
                logger.info(f"     {idx_def[:80]}...")
        else:
            logger.error("  ❌ NO INDEXES FOUND!")
        
        # Test 4: Index usage statistics
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: Index Usage Statistics")
        logger.info("=" * 70)
        
        cursor.execute("""
            SELECT 
                indexrelname as index_name,
                idx_scan as times_used,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            AND relname = 'portfolio_snapshots'
            ORDER BY idx_scan DESC
        """)
        
        stats = cursor.fetchall()
        if stats:
            logger.info(f"\n  {'Index Name':<35} {'Times Used':>12} {'Tuples Read':>15}")
            logger.info("  " + "-" * 65)
            for idx_name, times_used, tuples_read, tuples_fetched in stats:
                logger.info(f"  {idx_name:<35} {times_used:>12} {tuples_read:>15}")
            
            # Check if new indexes are being used
            new_indexes = ['idx_portfolio_paper_snapshot', 'idx_portfolio_snapshot_time_desc']
            for new_idx in new_indexes:
                found = False
                for idx_name, times_used, _, _ in stats:
                    if idx_name == new_idx:
                        found = True
                        if times_used == 0:
                            logger.warning(f"\n  ⚠️  {new_idx} has NEVER been used!")
                        else:
                            logger.info(f"\n  ✅ {new_idx} has been used {times_used} times")
                        break
                if not found:
                    logger.error(f"\n  ❌ {new_idx} NOT FOUND in stats!")
        else:
            logger.warning("  ⚠️  No index statistics found (tables may be empty)")
        
        # Test 5: ACTUAL query plan for dashboard stats
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: Dashboard Stats Query Plan (ACTUAL)")
        logger.info("=" * 70)
        
        logger.info("\n  Running EXPLAIN ANALYZE on dashboard stats query...")
        
        start = time.time()
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING) 
            SELECT 
                id, 
                snapshot_time, 
                total_value, 
                daily_pnl, 
                unrealized_pnl
            FROM portfolio_snapshots
            WHERE paper_trading = true 
            AND snapshot_time < NOW()
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)
        
        query_time = time.time() - start
        
        plan = cursor.fetchall()
        plan_text = '\n'.join([row[0] for row in plan])
        
        logger.info("\n" + plan_text)
        
        # Analyze the plan
        logger.info("\n  " + "=" * 66)
        logger.info("  ANALYSIS:")
        logger.info("  " + "=" * 66)
        
        if 'Seq Scan' in plan_text:
            logger.error("  ❌ SEQUENTIAL SCAN detected (BAD!)")
            logger.error("     Query is scanning entire table instead of using index")
            logger.error("     Possible causes:")
            logger.error("       - Table is too small (PostgreSQL prefers seq scan)")
            logger.error("       - Statistics are stale (run ANALYZE)")
            logger.error("       - Index doesn't match query pattern")
        elif 'Index Scan' in plan_text or 'Index Only Scan' in plan_text:
            logger.info("  ✅ INDEX SCAN detected (GOOD!)")
        else:
            logger.warning("  ⚠️  Unknown scan type")
        
        logger.info(f"\n  Query execution time: {query_time*1000:.1f}ms")
        
        if query_time > 1.0:
            logger.error(f"  ❌ Query is TOO SLOW ({query_time:.1f}s)")
        elif query_time > 0.1:
            logger.warning(f"  ⚠️  Query is slower than expected ({query_time*1000:.1f}ms)")
        else:
            logger.info(f"  ✅ Query is fast ({query_time*1000:.1f}ms)")
        
        # Test 6: Run ANALYZE and retest
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: Force Statistics Update")
        logger.info("=" * 70)
        
        logger.info("\n  Running ANALYZE on portfolio_snapshots...")
        cursor.execute("ANALYZE portfolio_snapshots")
        conn.commit()
        logger.info("  ✅ ANALYZE complete")
        
        logger.info("\n  Re-testing query after ANALYZE...")
        start = time.time()
        cursor.execute("""
            SELECT 
                id, 
                snapshot_time, 
                total_value, 
                daily_pnl, 
                unrealized_pnl
            FROM portfolio_snapshots
            WHERE paper_trading = true 
            AND snapshot_time < NOW()
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        query_time_after = time.time() - start
        
        logger.info(f"  Query time after ANALYZE: {query_time_after*1000:.1f}ms")
        
        if query_time_after < query_time * 0.5:
            logger.info(f"  ✅ Query is now {query_time/query_time_after:.1f}x faster!")
        elif query_time_after < query_time:
            logger.info(f"  ✅ Query improved slightly")
        else:
            logger.warning(f"  ⚠️  No improvement after ANALYZE")
        
        # Test 7: Check actual row count and data distribution
        logger.info("\n" + "=" * 70)
        logger.info("TEST 7: Data Distribution")
        logger.info("=" * 70)
        
        cursor.execute("""
            SELECT 
                paper_trading,
                COUNT(*) as count,
                MIN(snapshot_time) as earliest,
                MAX(snapshot_time) as latest
            FROM portfolio_snapshots
            GROUP BY paper_trading
        """)
        
        distribution = cursor.fetchall()
        logger.info(f"\n  {'paper_trading':<15} {'Count':>10} {'Earliest':>25} {'Latest':>25}")
        logger.info("  " + "-" * 80)
        for paper_trading, count, earliest, latest in distribution:
            logger.info(f"  {str(paper_trading):<15} {count:>10} {str(earliest):>25} {str(latest):>25}")
        
        # Final recommendations
        logger.info("\n" + "=" * 70)
        logger.info("RECOMMENDATIONS:")
        logger.info("=" * 70)
        
        if avg_latency > 0.1:
            logger.info("\n  1. HIGH NETWORK LATENCY DETECTED")
            logger.info("     - Consider using connection pooling (already implemented)")
            logger.info("     - Use Redis for caching (already implemented)")
            logger.info("     - Check Railway region (should match your location)")
            logger.info("     - ✅ Caching is the right solution for this")
        
        if query_time > 1.0:
            logger.info("\n  2. SLOW QUERY DETECTED")
            logger.info("     - Check if indexes are being used (see TEST 5)")
            logger.info("     - Verify table has data (see TEST 2)")
            logger.info("     - If Seq Scan: table may be too small (< 100 rows)")
            logger.info("     - ✅ Caching will mask the slow query issue")
        
        logger.info("\n  3. ALWAYS:")
        logger.info("     - Keep statistics updated with ANALYZE")
        logger.info("     - Monitor index usage over time")
        logger.info("     - Cache frequently accessed data (✅ implemented)")
        
        logger.info("\n" + "=" * 70)
        logger.info("DIAGNOSTICS COMPLETE")
        logger.info("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"\n❌ Error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

