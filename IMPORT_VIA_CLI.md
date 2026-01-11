# Import Database via Railway CLI

Since Railway's PostgreSQL service doesn't have a Query tab, we'll use Railway CLI to connect and import.

## Quick Steps

### Option 1: Interactive Import (Easiest)

1. **Run Railway CLI connect:**
   ```bash
   cd /Users/iabadvisors/ai-ml-trading-bot
   railway connect postgres
   ```

2. **This opens a psql shell.** Then paste the SQL content:
   
   Since the SQL file is already in your clipboard, just:
   - **Paste** (Cmd+V) the entire SQL into the psql shell
   - Press Enter
   - Wait for completion

3. **Verify import:**
   ```sql
   SELECT COUNT(*) FROM markets;  -- Should show 5
   SELECT COUNT(*) FROM predictions;  -- Should show 13
   \q  -- Exit psql
   ```

### Option 2: Direct File Import

If the interactive method doesn't work:

1. **Exit any existing psql session:**
   ```bash
   # If in psql, type: \q
   ```

2. **Import using file redirection:**
   ```bash
   cd /Users/iabadvisors/ai-ml-trading-bot
   cat local_db_backup_railway.sql | railway run psql
   ```

   OR if that doesn't work:
   ```bash
   railway shell --service postgres
   # Then in the shell:
   psql "$DATABASE_URL" < local_db_backup_railway.sql
   exit
   ```

### Option 3: Using Railway Variables

Get the DATABASE_URL from Railway and use it directly:

1. **In Railway Dashboard:**
   - Click on **"Variables"** tab in your PostgreSQL service
   - Find `DATABASE_URL` or construct from individual variables
   - Copy the value

2. **If it's a public URL** (not `.railway.internal`):
   ```bash
   psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
   ```

3. **If it's internal** (`.railway.internal`), use Railway CLI:
   ```bash
   railway connect postgres
   # Then paste SQL or use \i command
   ```

## Troubleshooting

### "railway connect postgres" doesn't find service
Try specifying the service name:
```bash
railway connect postgres --service postgres
```

Or check available services:
```bash
railway service
```

### Connection fails
1. Make sure Railway CLI is logged in: `railway login`
2. Make sure project is linked: `railway link`
3. Check Railway PostgreSQL service is running (should show "Online" in dashboard)

### SQL import fails with permission errors
- The SQL file has been pre-processed with `postgres` owner (Railway's default)
- Should work without permission issues
- If you get errors, let me know the exact error message

