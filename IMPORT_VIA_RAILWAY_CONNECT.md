# Import Database Using Railway Connect

The `postgres.railway.internal` host is only accessible from within Railway's network. We need to use Railway CLI's `connect` feature, which creates a tunnel.

## Method 1: Railway CLI Connect (Recommended)

Run these commands **in your own terminal** (interactive required):

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Connect to PostgreSQL via Railway CLI (this opens an interactive psql session)
railway connect postgres
```

Once connected, you'll be in a `psql` shell. Then run:

```sql
-- Import the SQL file (you'll need to exit psql first)
\q
```

Actually, since `railway connect` opens an interactive session, we need a different approach.

## Method 2: Use Railway Query Interface (Easiest - No Terminal Needed!)

1. **Go to Railway Dashboard**: https://railway.app
2. **Select project**: handsome-perception
3. **Click on your PostgreSQL service**
4. **Click "Query" or "Connect" tab** (should open a SQL query interface)
5. **Open your SQL file**: `local_db_backup_railway.sql`
6. **Copy all contents** (Select All, Copy)
7. **Paste into Railway's query interface**
8. **Click "Execute" or "Run"**

This will import all your data directly through Railway's web interface!

## Method 3: Use Railway Public URL (If Available)

Some Railway PostgreSQL services have a public connection URL. Check:

1. **Railway Dashboard** → **PostgreSQL Service** → **Settings** or **Variables**
2. **Look for `DATABASE_PUBLIC_URL`** or similar
3. This might look like: `postgresql://postgres:password@public-url.railway.app:5432/database`

If you find this, you can use:
```bash
./import_to_railway.sh "DATABASE_PUBLIC_URL_HERE"
```

## Method 4: Manual Connection with Individual Variables

From Railway Dashboard → PostgreSQL Service → Variables, get these individual values:

- `POSTGRES_USER` or `PGUSER` (usually `postgres`)
- `POSTGRES_PASSWORD` or `PGPASSWORD` (actual password)
- `POSTGRES_DB` or `PGDATABASE` (database name)
- `POSTGRES_HOST` or `PGHOST` (might be public URL)
- `POSTGRES_PORT` or `PGPORT` (usually `5432`)

If you get a **public host** (not `.railway.internal`), construct the URL:

```bash
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
./import_to_railway.sh "$DATABASE_URL"
```

## Recommendation

**Use Method 2 (Railway Query Interface)** - It's the easiest and doesn't require any terminal commands or connection string issues!



