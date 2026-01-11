# Get DATABASE_URL and Import Database

## Step 1: Get DATABASE_URL from Railway

1. **In Railway Dashboard** (where you are now):
   - Click on the **"Variables"** tab in your PostgreSQL service (Postgres)
   - Look for `DATABASE_URL` or `DATABASE_PUBLIC_URL`
   - **Copy the value** - it should look like:
     ```
     postgresql://postgres:password@interchange.proxy.rlwy.net:13955/railway
     ```
   - OR look for individual variables:
     - `POSTGRES_USER` or `PGUSER`
     - `POSTGRES_PASSWORD` or `PGPASSWORD`
     - `POSTGRES_HOST` or `PGHOST`
     - `POSTGRES_PORT` or `PGPORT`
     - `POSTGRES_DB` or `PGDATABASE`

2. **If you see `DATABASE_PUBLIC_URL`:**
   - This is perfect! Use this for the import

3. **If you only see `DATABASE_URL` with `.railway.internal`:**
   - We'll use Railway CLI instead (see Step 2)

## Step 2: Import Using DATABASE_URL

Once you have the `DATABASE_URL` (or `DATABASE_PUBLIC_URL`), run:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot
psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
```

Replace `YOUR_DATABASE_URL_HERE` with the actual URL from Railway.

**Example:**
```bash
psql "postgresql://postgres:yourpassword@interchange.proxy.rlwy.net:13955/railway" < local_db_backup_railway.sql
```

## Step 3: Verify Import

After import, verify the data:

```bash
psql "YOUR_DATABASE_URL_HERE" -c "SELECT COUNT(*) FROM markets;"
```

Should return: `5`

Or run all counts:
```bash
psql "YOUR_DATABASE_URL_HERE" -c "
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
"
```

## Alternative: Construct DATABASE_URL from Individual Variables

If Railway only has individual variables, construct the URL:

```bash
# Set variables (replace with actual values from Railway)
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="yourpassword"
POSTGRES_HOST="interchange.proxy.rlwy.net"  # or postgres.railway.internal
POSTGRES_PORT="13955"  # or 5432
POSTGRES_DB="railway"

# Construct URL and import
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
psql "$DATABASE_URL" < local_db_backup_railway.sql
```

## What to Look For in Railway Variables Tab

Go to: **Postgres service → Variables tab**

Look for these variables:

✅ **DATABASE_PUBLIC_URL** (best option - public connection)
- Format: `postgresql://user:pass@host:port/db`
- This is what you need!

✅ **DATABASE_URL** (might be internal or public)
- Check if host is `.railway.internal` (internal - use Railway CLI)
- Or public host like `interchange.proxy.rlwy.net` (public - can use directly)

✅ **Individual Variables:**
- `POSTGRES_USER` or `PGUSER`
- `POSTGRES_PASSWORD` or `PGPASSWORD`  
- `POSTGRES_HOST` or `PGHOST`
- `POSTGRES_PORT` or `PGPORT`
- `POSTGRES_DB` or `PGDATABASE`

---

## Next Steps

1. ✅ Go to Railway Dashboard → Postgres → Variables tab
2. ✅ Find `DATABASE_PUBLIC_URL` or `DATABASE_URL`
3. ✅ Copy the connection string
4. ✅ Run: `psql "YOUR_CONNECTION_STRING" < local_db_backup_railway.sql`
5. ✅ Verify import with SELECT queries

Let me know what you see in the Variables tab, and I'll help you import!

