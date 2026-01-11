# Quick Database Import to Railway

Since Railway CLI requires interactive selection, here are the **two easiest options**:

## Option 1: Use Railway Dashboard (Recommended - Easiest)

1. **Get your DATABASE_URL from Railway Dashboard:**
   - Go to your Railway project dashboard
   - Click on your **PostgreSQL service**
   - Go to the **"Variables"** tab
   - Copy the value of `DATABASE_URL` (it looks like: `postgresql://postgres:password@host:port/database`)

2. **Import the database locally:**
   ```bash
   psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
   ```
   Replace `YOUR_DATABASE_URL_HERE` with the actual `DATABASE_URL` from Railway.

## Option 2: Use Railway CLI Interactively

**Run this command in your own terminal** (not through the AI assistant):

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Link to project (will prompt you to select)
railway link

# Once linked, import the database
railway run psql < local_db_backup_railway.sql
```

## Option 3: Link by Project ID (If you know it)

If you know your Railway project ID, you can link non-interactively:

```bash
railway link --project YOUR_PROJECT_ID
```

To find your project ID:
- Go to Railway dashboard
- Select your project
- The URL will show something like: `https://railway.app/project/PROJECT_ID`
- Or run: `railway status` in a directory that's already linked

## Verify Import

After importing, verify the data:

```bash
# Using Railway CLI (if linked)
railway connect postgres
# Then in psql shell:
SELECT COUNT(*) FROM markets;  -- Should show 5
SELECT COUNT(*) FROM predictions;  -- Should show 13
SELECT COUNT(*) FROM signals;  -- Should show 13
SELECT COUNT(*) FROM trades;  -- Should show 13
```

Or using psql directly with DATABASE_URL:

```bash
psql "YOUR_DATABASE_URL_HERE" -c "SELECT COUNT(*) FROM markets;"
psql "YOUR_DATABASE_URL_HERE" -c "SELECT COUNT(*) FROM predictions;"
```

## Expected Results

After successful import:
- ✅ **markets**: 5 rows
- ✅ **predictions**: 13 rows  
- ✅ **signals**: 13 rows
- ✅ **trades**: 13 rows
- ✅ **portfolio_snapshots**: 1 row

## Troubleshooting

### "permission denied" or "role does not exist"
- Make sure you're using the correct `DATABASE_URL` from Railway
- The SQL file has been modified to use `postgres` as the owner

### "database does not exist"
- Check that your `DATABASE_URL` points to the correct database
- Railway may use a different database name than expected

### Connection timeout
- Make sure the Railway PostgreSQL service is running
- Check Railway logs for any issues

