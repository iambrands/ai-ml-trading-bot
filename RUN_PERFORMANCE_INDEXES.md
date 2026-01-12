# 🚀 Run Performance Indexes Migration

## Quick Start

### Option 1: Railway CLI (Recommended) ✅

```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Once connected, run:
\i src/database/migrations/002_performance_indexes.sql
```

**OR** copy-paste the SQL file contents directly into the psql prompt.

### Option 2: Using Script with DATABASE_URL

```bash
# Get DATABASE_URL from Railway dashboard:
# 1. Go to Railway Dashboard
# 2. Select PostgreSQL service
# 3. Go to "Variables" tab
# 4. Copy DATABASE_URL

# Set it and run:
export DATABASE_URL='your-railway-database-url-here'
./scripts/run_performance_indexes_railway.sh
```

### Option 3: Direct psql Command

```bash
# Get DATABASE_URL from Railway (see Option 2)
export DATABASE_URL='your-railway-database-url-here'
psql "$DATABASE_URL" -f src/database/migrations/002_performance_indexes.sql
```

## What This Migration Does

Adds critical database indexes for performance:

- ✅ `idx_predictions_market_timestamp` - Fast prediction lookups
- ✅ `idx_predictions_recent` - Recent predictions (last 7 days)
- ✅ `idx_signals_active_edge` - Active signals by edge
- ✅ `idx_trades_user_timestamp` - Trade history queries
- ✅ `idx_trades_status_entry_time` - Status-based queries
- ✅ Additional indexes for common query patterns

## Expected Output

You should see:
```
CREATE INDEX
CREATE INDEX
CREATE INDEX
...
ANALYZE
ANALYZE
...
```

If you see "already exists" messages, that's fine - it means the indexes were already created!

## Verification

After running, verify indexes were created:

```sql
-- Check indexes exist
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

## Performance Impact

After applying indexes:
- ✅ Query response times should be < 100ms (p95)
- ✅ Dashboard loading should be faster
- ✅ Better performance under load

