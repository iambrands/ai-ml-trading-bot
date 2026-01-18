# 🚨 CRITICAL: Run Database Migration NOW

**The dashboard timeout error will NOT be fixed until you run this migration!**

---

## ✅ FIXES ALREADY DEPLOYED (Code)

- ✅ Query optimization in `dashboard.py`
- ✅ 404 error handling in `polymarket.py`
- ✅ Relaxed market filtering in `polymarket.py`

## ❌ MISSING: Database Indexes

**The dashboard query is still slow because the indexes don't exist yet!**

---

## 🎯 STEP 1: Get the Migration SQL

**File**: `src/database/migrations/003_fix_dashboard_timeout.sql`

**Contents**:
```sql
-- Fix dashboard stats timeout by adding missing indexes
-- This migration fixes the "canceling statement due to statement timeout" error

-- Add composite index for dashboard stats query
-- Query: WHERE paper_trading = true AND snapshot_time < X ORDER BY snapshot_time DESC LIMIT 1
CREATE INDEX IF NOT EXISTS idx_portfolio_paper_snapshot 
ON portfolio_snapshots(paper_trading, snapshot_time DESC) 
WHERE paper_trading = true;

-- Add index on snapshot_time for sorting (if not exists)
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc 
ON portfolio_snapshots(snapshot_time DESC);

-- Add index on created_at if used in queries
CREATE INDEX IF NOT EXISTS idx_portfolio_created_at_desc 
ON portfolio_snapshots(created_at DESC);

-- Analyze table to update query planner statistics
ANALYZE portfolio_snapshots;

-- Verify indexes were created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'portfolio_snapshots'
ORDER BY indexname;
```

---

## 🎯 STEP 2: Apply Migration (Choose ONE Method)

### **Method A: Railway Dashboard (Easiest)** ⭐ RECOMMENDED

1. Go to **Railway Dashboard**: https://railway.app
2. Select your **PostgreSQL service** (not the web service)
3. Click the **"Query"** tab (or "Data" → "Query")
4. **Copy the SQL** from `src/database/migrations/003_fix_dashboard_timeout.sql` (above)
5. **Paste** into the query editor
6. Click **"Execute"** or **"Run"**
7. You should see:
   ```
   CREATE INDEX
   CREATE INDEX
   CREATE INDEX
   ANALYZE
   (indexes listed in results)
   ```

### **Method B: Railway CLI**

```bash
# Connect to PostgreSQL
railway connect postgres

# Then paste the SQL from the migration file
# (Copy from 003_fix_dashboard_timeout.sql)
# Type \q to exit
```

### **Method C: Direct psql (If you have DATABASE_URL)**

```bash
# Set your Railway DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Run migration
psql $DATABASE_URL -f src/database/migrations/003_fix_dashboard_timeout.sql
```

---

## ✅ STEP 3: Verify Indexes Were Created

**After running the migration, verify in Railway PostgreSQL Query tab**:

```sql
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'portfolio_snapshots'
ORDER BY indexname;
```

**Expected Output**:
```
idx_portfolio_paper_snapshot
idx_portfolio_snapshot_time_desc
idx_portfolio_created_at_desc
(plus any existing indexes)
```

**If you see these indexes, the migration worked!** ✅

---

## 🧪 STEP 4: Test Dashboard Stats Endpoint

**After migration is applied**:

```bash
# Test the endpoint
curl https://web-production-c490dd.up.railway.app/dashboard/stats

# Should return JSON in < 500ms (not timeout!)
```

**Expected**: Fast response with portfolio data  
**Before**: 30s timeout error  
**After**: < 500ms ✅

---

## 📊 EXPECTED RESULTS AFTER MIGRATION

| Metric | Before (No Indexes) | After (With Indexes) |
|--------|---------------------|----------------------|
| Dashboard Stats Query | **30s+ timeout** ❌ | **< 50ms** ✅ |
| Execution Plan | Full table scan | Index scan |
| Endpoint Response | 500 error | 200 OK with data |

---

## ❓ TROUBLESHOOTING

### "Index already exists"
✅ **Good!** This means the index was already created. Continue to Step 3.

### "Permission denied"
- Make sure you're connected to the **PostgreSQL service** (not web service)
- Make sure you're using an admin database user

### "Table does not exist"
- Check that `portfolio_snapshots` table exists:
  ```sql
  SELECT * FROM portfolio_snapshots LIMIT 1;
  ```

### Still timing out after migration?
1. Verify indexes exist (Step 3)
2. Check Railway logs for query performance
3. Try running `ANALYZE portfolio_snapshots;` again

---

## ⚡ QUICK REFERENCE

**Migration File**: `src/database/migrations/003_fix_dashboard_timeout.sql`  
**Railway Dashboard**: https://railway.app → PostgreSQL → Query  
**Test Endpoint**: `https://web-production-c490dd.up.railway.app/dashboard/stats`

---

**Status**: ⚠️ **MIGRATION REQUIRED** - Code fixes are deployed, but indexes must be created manually.

**After migration**: Dashboard will work perfectly! 🚀
