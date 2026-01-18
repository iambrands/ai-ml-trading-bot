# 🔍 Database Performance Diagnostics Guide

**Date**: January 18, 2026  
**Purpose**: Diagnose why indexes aren't being used despite migration

---

## 📋 Diagnostic Script

**File**: `scripts/diagnose_database.py`

**What it checks**:
1. **Network Latency** - Time to connect and query Railway PostgreSQL
2. **Table Sizes** - Row counts and disk usage for all tables
3. **Index Status** - Which indexes exist on `portfolio_snapshots`
4. **Index Usage** - Statistics showing if indexes are being used
5. **Query Execution Plan** - Actual plan for dashboard stats query
6. **Performance Before/After ANALYZE** - Impact of updating statistics
7. **Data Distribution** - How data is distributed in tables

---

## 🚀 How to Run

### Step 1: Set DATABASE_URL

```bash
export DATABASE_URL='postgresql://postgres:zTgqDKjcBkQcoyOhQsJAtmEWwigkXuMu@shuttle.proxy.rlwy.net:46223/railway'
```

### Step 2: Run Diagnostics

```bash
python3 scripts/diagnose_database.py
```

---

## 📊 Expected Output

### TEST 1: Network Latency
```
TEST 1: Network Latency
======================================================================
  Ping 1: 45.2ms
  Ping 2: 47.1ms
  ...
  Average latency: 46.3ms
```

**Analysis**:
- **< 50ms**: Good ✅
- **50-100ms**: Acceptable ⚠️
- **> 100ms**: High latency ❌ (may explain slow queries)

### TEST 2: Table Sizes
```
TEST 2: Table Sizes
======================================================================
  portfolio_snapshots       2 rows      48 kB
  markets                   5 rows      56 kB
  predictions            3400 rows     2.3 MB
  ...
```

**Analysis**:
- **Small tables (< 100 rows)**: PostgreSQL may prefer sequential scan
- **Large tables (> 1000 rows)**: Indexes should be used

### TEST 3: Index Status
```
TEST 3: Index Status on portfolio_snapshots
======================================================================
  ✅ idx_portfolio_paper_snapshot
     CREATE INDEX ... ON portfolio_snapshots(paper_trading, snapshot_time DESC) ...
```

**Analysis**:
- Should show all indexes created by migration
- If missing: Indexes weren't created

### TEST 4: Index Usage Statistics
```
TEST 4: Index Usage Statistics
======================================================================
  Index Name                           Times Used   Tuples Read
  -----------------------------------------------------------------
  idx_portfolio_paper_snapshot                  0              0
  idx_portfolio_snapshot_time_desc               0              0
```

**Analysis**:
- **0 times used**: Index exists but PostgreSQL isn't using it
- **Possible causes**:
  - Table is too small (seq scan is faster)
  - Statistics are stale
  - Query doesn't match index pattern

### TEST 5: Query Execution Plan
```
TEST 5: Dashboard Stats Query Plan (ACTUAL)
======================================================================
  Limit  (cost=0.28..8.31 rows=1 width=32) (actual time=0.123..0.123 rows=1 loops=1)
    ->  Index Scan using idx_portfolio_paper_snapshot ...
         ...

  ANALYSIS:
  ==================================================================
  ✅ INDEX SCAN detected (GOOD!)
  Query execution time: 0.123ms
  ✅ Query is fast (0.123ms)
```

**OR** (if index not used):
```
  Limit  (cost=... rows=1) (actual time=0.045..0.045 rows=1 loops=1)
    ->  Seq Scan on portfolio_snapshots ...
         ...

  ANALYSIS:
  ==================================================================
  ❌ SEQUENTIAL SCAN detected (BAD!)
  Query is scanning entire table instead of using index
```

**Analysis**:
- **Index Scan**: Index is being used ✅
- **Seq Scan**: Index not being used ❌
- **Why Seq Scan?**:
  - Table is small (< 100 rows)
  - Seq scan is faster for small tables
  - Statistics indicate seq scan is cheaper

### TEST 6: Before/After ANALYZE
```
TEST 6: Force Statistics Update
======================================================================
  Running ANALYZE on portfolio_snapshots...
  ✅ ANALYZE complete

  Re-testing query after ANALYZE...
  Query time after ANALYZE: 0.145ms
  ✅ Query improved slightly
```

---

## 🔍 Common Issues & Solutions

### Issue 1: High Network Latency (> 100ms)

**Symptoms**:
- Test 1 shows average latency > 100ms
- All queries slow, not just complex ones

**Solution**:
- ✅ **Caching is the right solution** (already implemented)
- Use connection pooling (already implemented)
- Check Railway region (should match your location)

### Issue 2: Sequential Scan on Small Tables

**Symptoms**:
- Test 2 shows `portfolio_snapshots` has < 10 rows
- Test 5 shows "Seq Scan" in query plan

**Why**:
- PostgreSQL prefers seq scan for small tables (< 100 rows)
- Seq scan is faster than index scan for small data

**Solution**:
- ✅ **This is expected behavior** - PostgreSQL is optimizing correctly
- ✅ **Caching will mask the issue** - users see fast cached responses
- As table grows (> 100 rows), PostgreSQL will switch to index scan automatically

### Issue 3: Indexes Not Being Used

**Symptoms**:
- Test 4 shows indexes have 0 uses
- Test 5 shows "Seq Scan" in query plan

**Why**:
- Table is too small
- Statistics are stale (needs ANALYZE)
- Query pattern doesn't match index

**Solution**:
- Run `ANALYZE` (Test 6 does this automatically)
- Wait for table to grow (> 100 rows)
- ✅ **Caching will mask the issue** regardless

### Issue 4: Stale Statistics

**Symptoms**:
- Test 5 shows "Seq Scan" but table has > 100 rows
- Test 6 shows improvement after ANALYZE

**Solution**:
- Run `ANALYZE` regularly (after bulk inserts)
- Already implemented in migration scripts
- PostgreSQL auto-analyzes but may be delayed

---

## ✅ Current Status

### Caching Solution (Already Implemented)

**Why it works**:
- First request: Slow (hits database, fills cache)
- Subsequent requests: **Fast** (< 100ms from cache)
- Cache TTL: 30-60 seconds

**Benefits**:
- **Masks database slowness** - users see fast responses
- Works regardless of index usage
- Reduces database load

**Expected Behavior**:
- First request: 40-75s (fills cache)
- Second request: **< 100ms** ✅ (from cache)

### Index Usage (May or May Not Be Used)

**Why indexes may not be used**:
- Table is small (< 100 rows) → PostgreSQL prefers seq scan
- This is **correct behavior** for small tables
- As table grows, indexes will be used automatically

**Solution**:
- ✅ **Caching handles this** - users see fast responses regardless
- Indexes are ready for when table grows
- No action needed if caching is working

---

## 🎯 Recommendations

### For Immediate Performance

1. ✅ **Use Caching** - Already implemented
   - Dashboard stats: 60s cache
   - Health: 30s cache
   - Markets: 30s cache

2. ✅ **Monitor Cache Hit Rate**
   - Check if subsequent requests are fast (< 100ms)
   - If yes: Caching is working ✅

### For Long-Term Performance

1. **Run ANALYZE Regularly**
   - After bulk inserts
   - Weekly maintenance
   - Already implemented in migration scripts

2. **Monitor Index Usage**
   - As table grows (> 100 rows), check if indexes are used
   - If still seq scan: May need query optimization

3. **Consider Redis for Multi-Instance**
   - Current cache is in-memory (single instance)
   - For multiple instances: Use Redis

---

## 📝 Next Steps

1. **Run Diagnostics**:
   ```bash
   python3 scripts/diagnose_database.py
   ```

2. **Test Endpoints After Deployment**:
   ```bash
   ./scripts/test_endpoints.sh
   ```

3. **Verify Cache is Working**:
   - First request: Slow (expected)
   - Second request: **Fast** (< 100ms) ✅

---

## 🎉 Success Criteria

✅ Endpoints responding (200 OK)  
✅ Cached requests: **< 100ms**  
✅ Diagnostic script runs without errors  
✅ Query plans show appropriate scan type (Index or Seq for small tables)  

---

**Status**: ✅ Diagnostic Script Ready  
**Next**: Run diagnostics to understand current state

