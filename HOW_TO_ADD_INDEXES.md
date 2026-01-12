# How to Add Database Indexes for Performance

## Overview

This guide will help you add database indexes to improve page load times from **60+ seconds to <2 seconds**.

The indexes will optimize queries that use `ORDER BY created_at DESC` and similar patterns.

---

## Step 1: Get Railway Database Connection String

1. **Go to Railway Dashboard**: https://railway.app/
2. **Click on your PostgreSQL service**
3. **Go to "Variables" tab**
4. **Copy the `DATABASE_URL`** value

The `DATABASE_URL` looks like:
```
postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway
```

---

## Step 2: Extract Connection Details (if needed)

If you need individual connection details, you can extract them from `DATABASE_URL`:
- **Host**: `postgres.railway.internal`
- **Port**: `5432`
- **Database**: `railway`
- **User**: `postgres`
- **Password**: (from `POSTGRES_PASSWORD` variable)

---

## Step 3: Connect to Railway Database

### Option A: Using Railway CLI (Recommended)

```bash
# Install Railway CLI if you haven't
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Connect to PostgreSQL
railway connect postgres
```

Then paste the SQL commands from `scripts/add_performance_indexes.sql`

### Option B: Using psql Directly

```bash
# Use the DATABASE_URL directly
psql "$DATABASE_URL" -f scripts/add_performance_indexes.sql
```

**Note**: This requires the DATABASE_URL to be publicly accessible, or you need to use Railway's TCP Proxy.

### Option C: Using Railway Web Interface

1. **Go to Railway Dashboard**
2. **Click on PostgreSQL service**
3. **Go to "Data" tab**
4. **Click "Query" button** (if available)
5. **Copy and paste the SQL from `scripts/add_performance_indexes.sql`**
6. **Run the query**

### Option D: Using Railway TCP Proxy

1. **Go to Railway Dashboard**
2. **Click on PostgreSQL service**
3. **Go to "Connect" tab**
4. **Find "TCP Proxy" section**
5. **Click "Generate Domain"**
6. **Use the provided connection string with psql**

---

## Step 4: Run the Index Script

The script is located at: `scripts/add_performance_indexes.sql`

### Using psql:

```bash
# If using Railway CLI tunnel
railway connect postgres
# Then paste the SQL commands

# Or if using DATABASE_URL directly
psql "$DATABASE_URL" -f scripts/add_performance_indexes.sql
```

### Using Railway Web Interface:

1. Copy the contents of `scripts/add_performance_indexes.sql`
2. Paste into Railway's query interface
3. Execute

---

## Step 5: Verify Indexes Were Created

Run this query to verify indexes were created:

```sql
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%_created_at%'
       OR indexname LIKE 'idx_%_entry_time%'
       OR indexname LIKE 'idx_%_snapshot_time%'
       OR indexname LIKE 'idx_%_prediction_time%'
ORDER BY tablename, indexname;
```

You should see indexes like:
- `idx_signals_created_at_desc`
- `idx_trades_entry_time_desc`
- `idx_portfolio_snapshot_time_desc`
- `idx_predictions_prediction_time_desc`
- etc.

---

## Expected Results

### Before Indexes:
- Page load time: **60+ seconds**
- Database queries: **Full table scans**
- ORDER BY queries: **Very slow**

### After Indexes:
- Page load time: **<2 seconds**
- Database queries: **Index scans**
- ORDER BY queries: **Fast**

---

## What the Indexes Do

The indexes optimize these query patterns:

1. **`ORDER BY created_at DESC`**:
   - Signals, Markets queries
   - Uses: `idx_signals_created_at_desc`, `idx_markets_created_at_desc`

2. **`ORDER BY entry_time DESC`**:
   - Trades queries
   - Uses: `idx_trades_entry_time_desc`

3. **`ORDER BY snapshot_time DESC`**:
   - Portfolio queries
   - Uses: `idx_portfolio_snapshot_time_desc`

4. **`ORDER BY prediction_time DESC`**:
   - Predictions queries
   - Uses: `idx_predictions_prediction_time_desc`

5. **Composite indexes**:
   - Optimize filtered queries (e.g., WHERE market_id = X ORDER BY created_at DESC)
   - Uses: `idx_signals_market_created_at`, `idx_trades_status_entry_time`, etc.

---

## Troubleshooting

### Index Already Exists

If you see "already exists" errors, that's fine - the script uses `CREATE INDEX IF NOT EXISTS`, so indexes won't be duplicated.

### Permission Denied

Make sure you're using the correct database user (usually `postgres`). Railway's `DATABASE_URL` should have the correct permissions.

### Connection Failed

- Check that `DATABASE_URL` is correct
- Try using Railway CLI tunnel instead
- Verify PostgreSQL service is running

---

## Rollback (if needed)

If you need to remove the indexes:

```sql
DROP INDEX IF EXISTS idx_signals_created_at_desc;
DROP INDEX IF EXISTS idx_trades_entry_time_desc;
DROP INDEX IF EXISTS idx_portfolio_snapshot_time_desc;
DROP INDEX IF EXISTS idx_predictions_prediction_time_desc;
DROP INDEX IF EXISTS idx_markets_created_at_desc;
DROP INDEX IF EXISTS idx_signals_market_created_at;
DROP INDEX IF EXISTS idx_signals_executed_created_at;
DROP INDEX IF EXISTS idx_trades_status_entry_time;
DROP INDEX IF EXISTS idx_trades_market_entry_time;
DROP INDEX IF EXISTS idx_predictions_market_prediction_time;
```

---

## Summary

1. ✅ Get Railway `DATABASE_URL`
2. ✅ Connect to database (CLI, psql, or web interface)
3. ✅ Run `scripts/add_performance_indexes.sql`
4. ✅ Verify indexes were created
5. ✅ Test page load times (should be <2 seconds)

The indexes are safe to add - they only improve query performance and don't modify data.

---

*Created: 2026-01-11*
*Script: scripts/add_performance_indexes.sql*

