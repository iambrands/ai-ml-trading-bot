# Quick Fix: Performance Slow Again

## ⚠️ Current Performance

**Test Results** (just now):
- Health: **67.4 seconds** ❌ (very slow)
- Predictions: 4.6 seconds ⚠️ (acceptable)
- Signals: **439.8 seconds** ❌ (very slow!)
- Trades: **40.4 seconds** ❌ (slow)
- Portfolio: **241.4 seconds** ❌ (very slow!)

**Previous Performance** (after indexes):
- Health: 13.3 seconds
- Predictions: 0.93 seconds ✅
- Signals: 26.8 seconds
- Trades: 1.23 seconds ✅
- Portfolio: 23.8 seconds

**Performance has degraded significantly!**

---

## 🔧 Quick Fix

### Re-run ANALYZE on Tables

The most likely cause is **stale query planner statistics**. PostgreSQL uses statistics to decide which indexes to use. When statistics are stale, it might not use indexes optimally.

**Solution**: Refresh statistics by running `ANALYZE`

```bash
# 1. Connect to Railway database
railway connect postgres

# 2. Run ANALYZE on all tables
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

# 3. Verify indexes still exist
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('signals', 'trades', 'portfolio_snapshots', 'predictions', 'markets')
GROUP BY tablename
ORDER BY tablename;
```

**Or use the script**:
```bash
railway connect postgres
\i /Users/iabadvisors/ai-ml-trading-bot/scripts/refresh_performance_indexes.sql
```

---

## 📋 What This Does

`ANALYZE` refreshes PostgreSQL's query planner statistics:
- Updates table statistics (row counts, data distribution)
- Updates index statistics (index usage patterns)
- Helps query planner choose optimal indexes

**This is safe and fast** - it doesn't modify data, just refreshes statistics.

---

## ⏱️ Expected Results

**After running ANALYZE**:
- Query planner should use indexes optimally
- Performance should improve significantly
- Should return to near previous performance levels

**Expected performance after ANALYZE**:
- Health: <1 second ✅
- Predictions: <2 seconds ✅
- Signals: <2 seconds ✅
- Trades: <2 seconds ✅
- Portfolio: <2 seconds ✅

---

## 🔍 Alternative Causes (if ANALYZE doesn't help)

1. **Indexes dropped** (unlikely)
   - Check with: `SELECT * FROM pg_indexes WHERE schemaname = 'public'`
   
2. **Much more data** (possible)
   - Check row counts
   - Even with indexes, very large tables can be slower
   
3. **Railway resource constraints** (possible)
   - Check Railway metrics (CPU, memory)
   - Database might be under resource pressure
   
4. **Connection pool exhausted** (possible)
   - Check connection counts
   - Too many connections can cause slow queries

---

## 📊 Next Steps

1. ✅ **Re-run ANALYZE** (quick fix - try this first)
2. ⏳ **Verify indexes exist** (check if they were dropped)
3. ⏳ **Check data volumes** (see if tables grew significantly)
4. ⏳ **Check Railway metrics** (resource constraints)
5. ⏳ **Check connection pool** (too many connections)

---

*Created: 2026-01-11*
*Issue: Performance degraded significantly*
*Quick Fix: Re-run ANALYZE on tables*

