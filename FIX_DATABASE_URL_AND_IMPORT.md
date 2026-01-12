# Fix DATABASE_URL and Import Database

## Problem
`DATABASE_URL` shows as: `postgresql://:@:/` (empty credentials)

## Solution: Use Individual Variables

Since `DATABASE_URL` is empty, we need to check individual PostgreSQL variables and construct the connection string.

## Step 1: Check Individual Variables in Railway

In Railway Dashboard → Postgres → Variables tab, look for these variables:

### Required Variables:
- `POSTGRES_USER` or `PGUSER` 
- `POSTGRES_PASSWORD` or `PGPASSWORD`
- `POSTGRES_HOST` or `PGHOST`
- `POSTGRES_PORT` or `PGPORT`
- `POSTGRES_DB` or `PGDATABASE`

### Also check for:
- `DATABASE_PUBLIC_URL` (might have a public connection string)
- Any variable with actual values (not empty)

## Step 2: Get Values from Variables Tab

Please check the **Variables** tab and share what you see. Look for:

1. **Username:** Should be `postgres` or similar
2. **Password:** Should be a long random string (Railway auto-generates)
3. **Host:** Might be `postgres.railway.internal` (internal) or `interchange.proxy.rlwy.net` (public)
4. **Port:** Should be `5432` or a number like `13955`
5. **Database:** Should be `railway` or `postgres`

## Step 3: Construct DATABASE_URL

Once you have the values, we can construct:

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

**Example:**
```
postgresql://postgres:abc123xyz@interchange.proxy.rlwy.net:13955/railway
```

## Step 4: Import Database

Once we have the proper connection string:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot
psql "postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE" < local_db_backup_railway.sql
```

## Alternative: Use Railway CLI Shell

If variables are internal (`.railway.internal`), we can use Railway CLI:

```bash
railway shell --service postgres
```

Then in the shell, Railway will have the resolved `DATABASE_URL` available, and we can import.

---

## What to Do Now

**Please check Railway → Postgres → Variables tab and tell me:**

1. Do you see `POSTGRES_USER` or `PGUSER`? What's the value?
2. Do you see `POSTGRES_PASSWORD` or `PGPASSWORD`? Is it empty or has a value?
3. Do you see `POSTGRES_HOST` or `PGHOST`? What's the value?
4. Do you see `POSTGRES_PORT` or `PGPORT`? What's the value?
5. Do you see `POSTGRES_DB` or `PGDATABASE`? What's the value?
6. Do you see `DATABASE_PUBLIC_URL`? What's its value?

Once I have these values, I can construct the proper connection string and import the database immediately!



