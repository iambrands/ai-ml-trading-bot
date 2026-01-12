# Import Database in psql Shell

## ✅ You're Connected!

Railway CLI connected successfully! You're now in a psql shell connected to Railway PostgreSQL.

## Step 1: Import Database

You have **two options** to import:

### Option A: Paste SQL File (Easiest)

The SQL file is already in your clipboard! Just:

1. **Paste** (Cmd+V) the entire SQL file content
2. Press **Enter**
3. Wait for completion

You'll see messages like:
- `CREATE TABLE ...`
- `COPY ...`
- `ALTER TABLE ...`
- etc.

Wait until you see `postgres=#` prompt again.

### Option B: Use \i Command

If pasting doesn't work, use the `\i` command:

```sql
\i /Users/iabadvisors/ai-ml-trading-bot/local_db_backup_railway.sql
```

Press Enter and wait for completion.

## Step 2: Verify Import

After import completes, verify the data:

```sql
-- Check row counts
SELECT 
    'markets' as table_name, COUNT(*) as rows FROM markets
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'trades', COUNT(*) FROM trades
UNION ALL
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots;
```

**Expected Output:**
```
table_name         | rows
-------------------+------
markets            |    5
predictions        |   13
signals            |   13
trades             |   13
portfolio_snapshots|    1
```

## Step 3: Exit psql

Once verified, exit:

```sql
\q
```

## Troubleshooting

### Import Errors

If you see errors during import:

1. **"relation already exists" errors:**
   - Tables might already exist
   - Check: `\dt` (list tables)
   - If tables exist, you might need to drop them first (we're importing fresh data anyway)

2. **Permission errors:**
   - Shouldn't happen - we're using `postgres` user
   - If you get errors, let me know the exact error message

3. **Import incomplete:**
   - Check if all tables were created: `\dt`
   - Check if data was imported: `SELECT COUNT(*) FROM markets;`

### If Import Fails

If import fails, you can try:

1. **Drop existing tables** (if they exist):
   ```sql
   DROP TABLE IF EXISTS trades CASCADE;
   DROP TABLE IF EXISTS signals CASCADE;
   DROP TABLE IF EXISTS predictions CASCADE;
   DROP TABLE IF EXISTS portfolio_snapshots CASCADE;
   DROP TABLE IF EXISTS feature_snapshots CASCADE;
   DROP TABLE IF EXISTS model_performance CASCADE;
   DROP TABLE IF EXISTS markets CASCADE;
   ```

2. **Then import again:**
   - Paste SQL file again
   - Or use `\i` command

## Quick Commands Reference

```sql
-- List tables
\dt

-- Check row counts
SELECT COUNT(*) FROM markets;  -- Should show 5

-- View a sample
SELECT * FROM markets LIMIT 5;

-- Exit psql
\q
```

## What to Do Now

**In your psql shell (which is already open):**

1. ✅ **Paste the SQL file** (Cmd+V) - it's in your clipboard
2. ✅ **Wait for completion** (will take a few seconds)
3. ✅ **Verify import** with SELECT queries
4. ✅ **Exit** with `\q`

**Or use \i command:**
```sql
\i /Users/iabadvisors/ai-ml-trading-bot/local_db_backup_railway.sql
```

Once import is complete, your Railway database will have all your data and be ready to use!



