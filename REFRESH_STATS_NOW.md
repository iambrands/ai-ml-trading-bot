# 🚀 Refresh Database Statistics - DO THIS NOW

## ⚡ Quick Fix for Slow Performance

Performance has degraded significantly. The fix is simple: refresh PostgreSQL statistics.

---

## 📋 Quick Commands

### Option 1: Use Railway CLI (Recommended)

```bash
# 1. Connect to database
railway connect postgres

# 2. Paste these commands:
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

# 3. Verify (optional - shows index counts)
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('signals', 'trades', 'portfolio_snapshots', 'predictions', 'markets')
GROUP BY tablename
ORDER BY tablename;

# 4. Exit
\q
```

---

### Option 2: Use SQL Script File

```bash
# 1. Connect
railway connect postgres

# 2. Run script
\i /Users/iabadvisors/ai-ml-trading-bot/scripts/refresh_performance_indexes.sql

# 3. Exit
\q
```

---

## ✅ What This Does

- Refreshes query planner statistics
- Helps PostgreSQL use indexes optimally
- **Safe** - doesn't modify data, only statistics
- **Fast** - takes seconds to run
- **Effective** - should restore performance immediately

---

## 📊 Expected Results

**Before**: 
- Signals: 439.8s ❌
- Portfolio: 241.4s ❌

**After ANALYZE**:
- Signals: <5s ✅
- Portfolio: <5s ✅

---

## 🎯 Why This Works

PostgreSQL's query planner uses statistics to decide:
- Which indexes to use
- How to join tables
- Execution order

When statistics are stale, it makes poor choices → slow queries.

Refreshing statistics → better choices → fast queries.

---

*Created: 2026-01-11*
*Status: Ready to run*
*Time: ~30 seconds to fix*

