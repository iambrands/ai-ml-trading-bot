# Get Resolved DATABASE_URL from Railway

The `DATABASE_URL` you provided looks like a template: `postgresql://:@postgres.railway.internal:5432/`

Railway resolves template variables at runtime. Here's how to get the **actual resolved values**:

## Method 1: Railway Dashboard (Easiest)

1. **Go to Railway Dashboard**: https://railway.app
2. **Select project**: handsome-perception
3. **Click on your PostgreSQL service** (might be named "Postgres" or similar)
4. **Go to "Variables" tab**
5. **Look for `DATABASE_URL`** - it should show the **resolved** value with actual:
   - Username (usually `postgres`)
   - Password (actual password)
   - Database name (usually `railway` or `postgres`)

   Example resolved DATABASE_URL:
   ```
   postgresql://postgres:actualpassword@postgres.railway.internal:5432/railway
   ```

6. **Copy the resolved DATABASE_URL**

## Method 2: Railway CLI Interactive (If you can run in your terminal)

Run this in your **own terminal** (interactive):

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Option A: Connect to PostgreSQL directly
railway connect postgres

# Option B: Get variables from shell
railway shell
# Then in the shell:
echo $DATABASE_URL
exit
```

## Method 3: Get Individual Variables

If `DATABASE_URL` isn't resolved, get individual variables and construct it:

From Railway Dashboard → PostgreSQL Service → Variables:
- `PGUSER` or `POSTGRES_USER` (usually `postgres`)
- `POSTGRES_PASSWORD` (actual password)
- `PGDATABASE` or `POSTGRES_DB` (usually `railway` or `postgres`)
- `PGHOST` or `POSTGRES_HOST` (should be `postgres.railway.internal`)
- `PGPORT` or `POSTGRES_PORT` (usually `5432`)

Then construct:
```
postgresql://POSTGRES_USER:POSTGRES_PASSWORD@POSTGRES_HOST:POSTGRES_PORT/POSTGRES_DB
```

## Once You Have the Resolved DATABASE_URL

Run the import:

```bash
./import_to_railway.sh "postgresql://postgres:actualpassword@postgres.railway.internal:5432/railway"
```

Or manually:
```bash
psql "postgresql://postgres:actualpassword@postgres.railway.internal:5432/railway" < local_db_backup_railway.sql
```

## Alternative: Use Railway Query Interface

If you can't get the DATABASE_URL, use Railway's web interface:

1. Go to Railway Dashboard
2. Select PostgreSQL service
3. Click "Connect" or "Query" tab
4. Paste the contents of `local_db_backup_railway.sql`
5. Click "Execute"

This will run the SQL directly in Railway's interface.

