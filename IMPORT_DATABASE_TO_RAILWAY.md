# Import Database to Railway - Step by Step

## ✅ Prerequisites Ready

- ✅ Railway service is working
- ✅ SQL file ready: `local_db_backup_railway.sql` (707 lines, 24KB)
- ✅ All owner references fixed (14 references → `postgres`)
- ✅ Railway project linked: handsome-perception

## Method 1: Railway Web Interface (Easiest - Recommended)

This is the easiest method and doesn't require any terminal commands or connection strings.

### Steps:

1. **Open Railway Dashboard:**
   - Go to: https://railway.app
   - Select project: **handsome-perception**
   - Click on your **PostgreSQL service** (not Web Service)

2. **Open Query Interface:**
   - Click on **"Query"** tab (or "Connect" tab - look for SQL query interface)
   - This opens a web-based PostgreSQL query interface

3. **Import SQL File:**
   - Open your SQL file: `local_db_backup_railway.sql`
   - **Select All** (Cmd+A on Mac, Ctrl+A on Windows)
   - **Copy** (Cmd+C on Mac, Ctrl+C on Windows)
   - **Paste** into Railway's query interface (Cmd+V / Ctrl+V)
   - Click **"Execute"** or **"Run"** button

4. **Verify Import:**
   - After execution, you should see success messages
   - Run these queries to verify:
     ```sql
     SELECT COUNT(*) FROM markets;  -- Should show 5
     SELECT COUNT(*) FROM predictions;  -- Should show 13
     SELECT COUNT(*) FROM signals;  -- Should show 13
     SELECT COUNT(*) FROM trades;  -- Should show 13
     SELECT COUNT(*) FROM portfolio_snapshots;  -- Should show 1
     ```

---

## Method 2: Railway CLI Connect (If Web Interface Not Available)

If Railway doesn't have a Query tab, use Railway CLI:

### Steps:

1. **Connect to PostgreSQL via Railway CLI:**
   ```bash
   cd /Users/iabadvisors/ai-ml-trading-bot
   railway connect postgres
   ```
   
   This opens an interactive `psql` shell connected to Railway PostgreSQL.

2. **Import SQL File:**
   ```sql
   -- In the psql shell:
   \i /Users/iabadvisors/ai-ml-trading-bot/local_db_backup_railway.sql
   ```
   
   OR if the path doesn't work, exit and use:
   ```bash
   # Exit psql shell first
   \q
   
   # Then import from terminal
   cat local_db_backup_railway.sql | railway connect postgres
   ```

3. **Verify Import:**
   ```bash
   railway connect postgres
   # Then in psql:
   SELECT COUNT(*) FROM markets;
   \q
   ```

---

## Method 3: Using DATABASE_URL (If Public Connection Available)

If Railway provides a public `DATABASE_URL` (not `.railway.internal`):

1. **Get DATABASE_URL from Railway Dashboard:**
   - Go to PostgreSQL service → **Variables** tab
   - Look for `DATABASE_PUBLIC_URL` or check if `DATABASE_URL` has a public host

2. **Import using psql:**
   ```bash
   psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
   ```

3. **Verify:**
   ```bash
   psql "YOUR_DATABASE_URL_HERE" -c "SELECT COUNT(*) FROM markets;"
   ```

---

## Method 4: Railway CLI Shell (Alternative)

Use Railway CLI shell to import:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Open Railway shell with PostgreSQL service variables
railway shell --service [your-postgres-service-name]

# In the shell, import the database
psql "$DATABASE_URL" < local_db_backup_railway.sql

# Or if DATABASE_URL isn't set, construct it:
psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB" < local_db_backup_railway.sql
```

---

## Expected Results After Import

After successful import, you should have:

- ✅ **markets**: 5 rows
- ✅ **predictions**: 13 rows
- ✅ **signals**: 13 rows
- ✅ **trades**: 13 rows
- ✅ **portfolio_snapshots**: 1 row

---

## Verify Data is Accessible

After importing, verify your Web Service can access the data:

1. **Check Railway Web Service logs:**
   - Should see: `Database engine created successfully`
   - No connection errors

2. **Test API endpoints:**
   ```bash
   # Get your Railway app URL from Railway dashboard
   curl https://your-app.railway.app/api/markets
   curl https://your-app.railway.app/api/predictions
   curl https://your-app.railway.app/api/signals
   ```

   Should return JSON with your data.

---

## Troubleshooting

### "Query tab not found" in Railway
- Some Railway PostgreSQL services don't have Query tab
- Use Method 2 (Railway CLI Connect) instead

### "railway connect postgres" fails
- Make sure Railway CLI is logged in: `railway login`
- Make sure project is linked: `railway link`
- Try specifying service: `railway connect postgres --service [service-name]`

### Import fails with "permission denied"
- Make sure SQL file uses `postgres` as owner (already fixed ✅)
- Check that Railway PostgreSQL user is `postgres`
- Try running with Railway CLI which has proper permissions

### Connection timeout
- Railway internal host (`postgres.railway.internal`) is only accessible from Railway network
- Use Railway CLI or web interface (they're already on Railway network)
- Don't try to connect from local machine to `.railway.internal` host

---

## Next Steps After Import

1. ✅ Database imported successfully
2. ✅ Verify data in Railway (run SELECT queries)
3. ✅ Test Web Service API endpoints
4. ✅ Check Railway logs for any errors
5. ✅ Your app should now display real data in the UI!

---

## Quick Reference

**SQL File:** `local_db_backup_railway.sql` (24KB, 707 lines)

**Recommended Method:** Railway Web Interface (Method 1) - Easiest, no terminal needed

**Expected Data:**
- 5 markets
- 13 predictions
- 13 signals
- 13 trades
- 1 portfolio snapshot



