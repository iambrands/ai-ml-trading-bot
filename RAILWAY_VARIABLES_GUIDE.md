# Railway Variables - What to Look For

## DATABASE_URL is Empty

You're seeing: `postgresql://:@:/`

This means Railway hasn't populated it yet, or it needs individual variables.

## Step 1: Check Variables Tab

Go to: **Railway Dashboard → Postgres service → Variables tab**

### Look for These Variables:

#### Option A: Individual PostgreSQL Variables

1. **POSTGRES_USER** or **PGUSER**
   - Value should be: `postgres`
   - If missing or empty, use: `postgres`

2. **POSTGRES_PASSWORD** or **PGPASSWORD**
   - Railway auto-generates this
   - Should be a long random string
   - **IMPORTANT:** Copy this exact value
   - If empty, Railway might need to regenerate it

3. **POSTGRES_HOST** or **PGHOST**
   - Could be:
     - `postgres.railway.internal` (internal - only works from Railway network)
     - `interchange.proxy.rlwy.net` (public - can connect from anywhere)
     - Or similar public proxy URL
   - **We need the PUBLIC one** for importing from your local machine

4. **POSTGRES_PORT** or **PGPORT**
   - Could be: `5432` (standard PostgreSQL)
   - Or: `13955` or similar (Railway proxy port)
   - Copy the exact number

5. **POSTGRES_DB** or **PGDATABASE**
   - Usually: `railway` or `postgres`
   - If missing, try: `railway`

#### Option B: Public Connection URL

Look for:
- **DATABASE_PUBLIC_URL** - This would be perfect!
- Format: `postgresql://postgres:password@interchange.proxy.rlwy.net:13955/railway`

## Step 2: If Variables Are Missing

If variables are empty or missing:

1. **Railway might need to generate them**
   - Try redeploying the PostgreSQL service
   - Or check Railway logs for auto-generated values

2. **Check Railway's public connection URL**
   - In Railway Dashboard → Postgres → **Settings** tab
   - Look for "Connection" or "Public URL" section
   - Railway often provides a public connection URL separately

## Step 3: Construct Connection String

Once you have the values:

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

**Example:**
```
postgresql://postgres:abc123xyz@interchange.proxy.rlwy.net:13955/railway
```

## Step 4: Import Using Script

I've created an interactive script for you:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot
./import_via_railway_web.sh
```

This script will:
1. Prompt you for each value
2. Construct the connection string
3. Import the database
4. Verify the import

## Alternative: Railway CLI Interactive

If variables don't work, use Railway CLI in your own terminal:

```bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Connect to PostgreSQL (interactive - run in your terminal)
railway connect postgres
```

Then in the psql shell:
- Paste the SQL file contents (it's in your clipboard)
- Or type: `\i /Users/iabadvisors/ai-ml-trading-bot/local_db_backup_railway.sql`

## What to Check Now

**Go to Railway Dashboard → Postgres → Variables tab and check:**

1. ✅ Do you see `POSTGRES_PASSWORD` with an actual value? (not empty)
2. ✅ Do you see `POSTGRES_HOST`? Is it `.railway.internal` or a public URL?
3. ✅ Do you see `POSTGRES_PORT`? What's the number?
4. ✅ Do you see `DATABASE_PUBLIC_URL`? (best option!)

**Once you have these values, run:**
```bash
./import_via_railway_web.sh
```

This will guide you through the import interactively!

