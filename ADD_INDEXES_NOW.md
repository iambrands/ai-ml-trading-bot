# Quick Guide: Add Database Indexes NOW

## ✅ Railway CLI Setup Confirmed

- Railway CLI: ✅ Installed
- Authentication: ✅ Logged in
- Project: ✅ Linked
- SQL Script: ✅ Ready

---

## 🚀 Execute (Choose One Method)

### Method 1: Railway CLI (Interactive - RECOMMENDED)

This is the **easiest and most reliable** method:

```bash
# 1. Connect to PostgreSQL
railway connect postgres

# 2. Once connected, copy and paste this entire SQL block:

-- Add performance indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_signals_created_at_desc ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time_desc ON trades(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc ON portfolio_snapshots(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction_time_desc ON predictions(prediction_time DESC);
CREATE INDEX IF NOT EXISTS idx_markets_created_at_desc ON markets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_market_created_at ON signals(market_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_executed_created_at ON signals(executed, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status_entry_time ON trades(status, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_market_entry_time ON trades(market_id, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_market_prediction_time ON predictions(market_id, prediction_time DESC);
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

# 3. Press Enter to execute
# 4. You should see "CREATE INDEX" messages
# 5. Type \q to exit
```

**Time**: ~30 seconds

---

### Method 2: Copy SQL File Content

The SQL is in: `scripts/add_performance_indexes.sql`

You can:
1. Open the file in your editor
2. Copy all contents
3. Paste into `railway connect postgres` session

---

## ✅ Verification

After running the SQL, verify indexes were created:

```sql
-- In Railway CLI psql session:
SELECT 
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
    AND (indexname LIKE 'idx_%_created_at%'
         OR indexname LIKE 'idx_%_entry_time%'
         OR indexname LIKE 'idx_%_snapshot_time%'
         OR indexname LIKE 'idx_%_prediction_time%')
ORDER BY tablename, indexname;
```

You should see ~10 indexes listed.

---

## 📊 Expected Results

**Before Indexes**: 60+ seconds page load
**After Indexes**: <2 seconds page load ✅

---

## ⚡ Quick Copy-Paste SQL

Here's the SQL ready to paste:

```sql
CREATE INDEX IF NOT EXISTS idx_signals_created_at_desc ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time_desc ON trades(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc ON portfolio_snapshots(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction_time_desc ON predictions(prediction_time DESC);
CREATE INDEX IF NOT EXISTS idx_markets_created_at_desc ON markets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_market_created_at ON signals(market_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_executed_created_at ON signals(executed, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status_entry_time ON trades(status, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_market_entry_time ON trades(market_id, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_market_prediction_time ON predictions(market_id, prediction_time DESC);
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;
```

---

*Created: 2026-01-11*
*Status: Ready to Execute*

