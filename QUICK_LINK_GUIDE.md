# Quick Guide: Link PostgreSQL to Web Service

Since you already have PostgreSQL set up on Railway, here's exactly what to do:

## Step 1: Find Your PostgreSQL Service Name

1. In Railway Dashboard, look at your services list
2. You'll see your `web` service and your PostgreSQL service
3. **Note the exact name** of your PostgreSQL service (it might be "Postgres", "postgres", "PostgreSQL", etc.)
   - It's case-sensitive!
   - Look exactly as it appears in Railway

## Step 2: Add Variables to Web Service

1. **Go to your `web` service** (NOT the PostgreSQL service)
2. **Click "Variables" tab**
3. **Add these 5 variables** one by one:

   Click **"+ New Variable"** and add:

   | Variable Name | Value (Important: Replace `Postgres` with YOUR actual service name) |
   |--------------|-------------------------------------------------------------------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **Important Notes**:
   - Replace `Postgres` with your actual PostgreSQL service name
   - If your service is named `postgres` (lowercase), use: `${{postgres.PGHOST}}`
   - If it's `PostgreSQL`, use: `${{PostgreSQL.PGHOST}}`
   - Railway will automatically resolve these at runtime

4. **After adding all 5 variables**, Railway will automatically redeploy your web service

## Step 3: Verify Connection

1. **Check your web service deployment logs**
2. **Look for**: "Database engine created successfully"
3. **Should NOT see**: "[Errno 111] Connection refused" errors

If you see connection errors, check:
- Did you add all 5 variables?
- Did you use the correct service name in the variable values?
- Is your PostgreSQL service running? (should have green checkmark)

## Step 4: Import Your Database Backup

Once connected, import your data. **Easiest method using Railway's Web Interface**:

1. **Go to your PostgreSQL service** in Railway
2. **Click on "Data" tab** (or "Connect" tab)
3. **Look for SQL editor or Query interface**
4. **Open your local file**: `local_db_backup_20260110_140827.sql`
5. **Copy all contents** (707 lines)
6. **Paste into Railway's SQL editor**
7. **Click "Run" or "Execute"**

**Or using Railway CLI**:

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login and link
railway login
railway link

# Connect to PostgreSQL
railway connect postgres

# Once connected, you can paste the SQL content directly
# (Copy contents of local_db_backup_20260110_140827.sql and paste)
```

## What Should Happen

After adding variables and importing:

1. ✅ **Web service connects to PostgreSQL** - No more connection errors
2. ✅ **Your 5 markets are imported** - Data is in Railway database
3. ✅ **API endpoints return data** - `/predictions`, `/signals`, `/trades` show your data
4. ✅ **Models are available** - Already in Railway from git

## Troubleshooting

**If variables don't work**:
- Make sure service name matches exactly (case-sensitive)
- Check PostgreSQL service → Variables tab to see exact variable names
- The syntax is: `${{ServiceName.VARIABLE}}`

**If can't connect**:
- Verify all 5 variables are added to web service
- Check PostgreSQL service is running (green checkmark)
- Check deployment logs for specific errors

**If can't import**:
- Use Railway's web SQL editor (easiest)
- Or use Railway CLI: `railway connect postgres`
- Then paste SQL content directly


