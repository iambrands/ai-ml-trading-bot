# Performance Slow Again - Troubleshooting Guide

## Issue

**Reported**: System running slow again after 2 hours  
**Previous Fix**: Database indexes applied (improved performance significantly)  
**Status**: Investigating

---

## Possible Causes

### 1. Indexes Need Refresh (Most Likely)

**Issue**: PostgreSQL query planner statistics might be stale

**Solution**: Run `ANALYZE` again on tables

**Check**: Query execution plans might not be using indexes optimally

---

### 2. More Data Accumulated

**Issue**: As data grows, queries take longer even with indexes

**Solution**: 
- Check data volumes (how many rows in each table)
- Consider pagination/limits if not already applied
- Add more specific indexes if needed

---

### 3. Missing Indexes on Other Query Patterns

**Issue**: Some queries might use patterns we didn't index

**Solution**: Check slow queries and add indexes

**Check**: Look at query patterns in API endpoints

---

### 4. Railway Resource Constraints

**Issue**: Railway database or service might have resource limits

**Solution**:
- Check Railway metrics (CPU, memory, database connections)
- Upgrade Railway plan if needed
- Check for connection pooling issues

---

### 5. Database Connection Pooling

**Issue**: Connection pool might be exhausted

**Solution**: Check connection pool settings

---

## Quick Checks

### 1. Verify Indexes Are Still There

```sql
-- Connect to Railway database
railway connect postgres

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND (indexname LIKE 'idx_%_created_at%'
         OR indexname LIKE 'idx_%_entry_time%'
         OR indexname LIKE 'idx_%_snapshot_time%'
         OR indexname LIKE 'idx_%_prediction_time%')
ORDER BY tablename, indexname;
```

**Expected**: Should see ~10 indexes we created

---

### 2. Check Table Statistics (ANALYZE)

```sql
-- Run ANALYZE to refresh statistics
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;
```

**Why**: Query planner uses statistics to decide if indexes should be used. Stale statistics can cause slow queries.

---

### 3. Check Data Volumes

```sql
-- Check row counts
SELECT 
    'markets' as table_name, COUNT(*) as row_count FROM markets
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'trades', COUNT(*) FROM trades
UNION ALL
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots;
```

**Check**: If tables have grown significantly, queries might be slower even with indexes.

---

### 4. Check Slow Queries

**Option 1: Enable PostgreSQL slow query log**

Check Railway logs for slow queries

**Option 2: Check query patterns**

Look at API endpoints for queries that might not be optimized

---

## Recommended Actions

### Step 1: Re-run ANALYZE (Quick Fix)

```bash
railway connect postgres
```

Then in psql:
```sql
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;
```

**Why**: Refreshes query planner statistics, which can improve query performance significantly.

---

### Step 2: Check Current Performance

Run performance tests to see which endpoints are slow:

```bash
# Test each endpoint
curl -w "@-" -o /dev/null -s "https://web-production-c490dd.up.railway.app/health"
curl -w "@-" -o /dev/null -s "https://web-production-c490dd.up.railway.app/predictions?limit=50"
curl -w "@-" -o /dev/null -s "https://web-production-c490dd.up.railway.app/signals?limit=50"
curl -w "@-" -o /dev/null -s "https://web-production-c490dd.up.railway.app/trades?limit=50"
curl -w "@-" -o /dev/null -s "https://web-production-c490dd.up.railway.app/portfolio/latest"
```

Compare with previous performance test results.

---

### Step 3: Check Railway Metrics

1. Go to Railway Dashboard
2. Click on your database service
3. Check "Metrics" tab:
   - CPU usage
   - Memory usage
   - Connection count
   - Query performance

**Look for**:
- High CPU usage → Resource constraints
- High connection count → Connection pool issues
- Slow queries → Missing indexes or stale statistics

---

### Step 4: Check for Missing Indexes

Review API endpoints for query patterns we might have missed:

1. **Filtered queries**: WHERE clauses we didn't index
2. **Join queries**: Queries joining multiple tables
3. **Aggregation queries**: GROUP BY, COUNT, SUM, etc.

**Example**: If we see queries like:
```sql
SELECT * FROM signals WHERE market_id = X AND executed = false ORDER BY created_at DESC
```

We might need a composite index: `(market_id, executed, created_at DESC)`

---

## Quick Fix Script

Create a script to re-analyze tables:

```sql
-- Re-analyze all tables
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

-- Verify indexes
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('signals', 'trades', 'portfolio_snapshots', 'predictions', 'markets')
GROUP BY tablename
ORDER BY tablename;
```

---

## Summary

**Most Likely Fix**: Re-run `ANALYZE` on tables to refresh statistics

**Quick Action**:
```bash
railway connect postgres
```

Then:
```sql
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;
```

**Next Steps**:
1. ✅ Re-run ANALYZE (quick fix)
2. ⏳ Check current performance
3. ⏳ Check Railway metrics
4. ⏳ Check for missing indexes if still slow

---

*Created: 2026-01-11*
*Issue: Performance slow again after 2 hours*
*Status: Troubleshooting*


