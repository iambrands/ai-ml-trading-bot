# 🚀 Run Database Migration - Quick Guide

## Migration Will Add:
- ✅ `alerts` table (for notifications)
- ✅ `alert_history` table (alert tracking)
- ✅ `analytics_cache` table (performance optimization)
- ✅ `paper_trading` column on `trades` table
- ✅ `paper_trading` column on `portfolio_snapshots` table

## Method 1: Railway CLI (Easiest) ✅

```bash
# Connect to Railway database
railway connect postgres

# Once connected, run:
\i src/database/migrations/add_alerts_and_paper_trading.sql

# Or copy-paste the SQL directly:
```

Then copy the contents of `src/database/migrations/add_alerts_and_paper_trading.sql` and paste into the psql prompt.

## Method 2: Using psql with DATABASE_URL

### Step 1: Get DATABASE_URL from Railway
1. Go to Railway Dashboard
2. Click on your **PostgreSQL service**
3. Click **"Variables"** tab
4. Copy the `DATABASE_URL` value

### Step 2: Run Migration
```bash
# Set DATABASE_URL
export DATABASE_URL='your-connection-string-here'

# Run migration
psql "$DATABASE_URL" -f src/database/migrations/add_alerts_and_paper_trading.sql
```

Or use the script:
```bash
export DATABASE_URL='your-connection-string-here'
./scripts/run_migration_railway.sh
```

## Method 3: Railway Web Interface

If Railway has a SQL query interface:
1. Go to PostgreSQL service in Railway
2. Look for "Query" or "SQL" tab
3. Copy contents of `src/database/migrations/add_alerts_and_paper_trading.sql`
4. Paste and run

## Verification

After running, verify with:
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('alerts', 'alert_history', 'analytics_cache');

-- Check columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'trades' AND column_name = 'paper_trading';

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'portfolio_snapshots' AND column_name = 'paper_trading';
```

## Expected Output

You should see:
```
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE INDEX
ALTER TABLE
CREATE INDEX
ALTER TABLE
CREATE INDEX
CREATE TABLE
CREATE INDEX
```

If you see "already exists" messages, that's fine - it means the migration was already run!

