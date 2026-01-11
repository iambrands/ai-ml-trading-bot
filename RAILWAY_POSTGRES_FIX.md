# Fix Railway PostgreSQL Connection

## Problem

Railway PostgreSQL service has empty username/password in `DATABASE_URL`:
```
postgresql://:@postgres.railway.internal:5432/
```

The application cannot connect because credentials are missing.

## Solution

Railway PostgreSQL uses default credentials. We need to either:
1. **Set proper credentials in Railway** (Recommended)
2. **Use Railway's default connection method**

## Option 1: Set Credentials in Railway (Recommended)

### Step 1: Check Railway PostgreSQL Variables

1. Go to Railway Dashboard → **handsome-perception** project
2. Click on your **PostgreSQL service**
3. Go to **"Variables"** tab
4. Look for these variables:
   - `POSTGRES_USER` or `PGUSER` (should be set)
   - `POSTGRES_PASSWORD` or `PGPASSWORD` (should be set)
   - `POSTGRES_DB` or `PGDATABASE` (should be set)

### Step 2: Set Missing Variables

If any are missing or empty, **add them manually**:

1. In Railway PostgreSQL service → **Variables** tab
2. Click **"+ New Variable"**
3. Add these variables:

   ```
   Variable: POSTGRES_USER
   Value: postgres
   ```

   ```
   Variable: POSTGRES_PASSWORD
   Value: [generate a secure password - Railway will auto-generate one]
   ```

   ```
   Variable: POSTGRES_DB
   Value: railway
   ```

   Or Railway might already have these - check `${{Postgres.PGUSER}}` etc.

### Step 3: Update DATABASE_URL in Web Service

1. Go to your **Web Service** (not PostgreSQL service)
2. Go to **"Variables"** tab
3. Make sure these variables are **linked from PostgreSQL service**:
   - `POSTGRES_USER` → `${{Postgres.PGUSER}}`
   - `POSTGRES_PASSWORD` → `${{Postgres.PGPASSWORD}}`
   - `POSTGRES_DB` → `${{Postgres.PGDATABASE}}`
   - `POSTGRES_HOST` → `${{Postgres.PGHOST}}`
   - `POSTGRES_PORT` → `${{Postgres.PGPORT}}`

4. **Update or add `DATABASE_URL`** in your Web Service:
   ```
   Variable: DATABASE_URL
   Value: postgresql://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
   ```

### Step 4: Redeploy Web Service

After setting variables:
1. Railway should auto-redeploy your web service
2. Or manually trigger a redeploy from Railway dashboard
3. Check logs to verify database connection

## Option 2: Use Individual Variables (Already Configured)

Your app is already configured to use individual variables if `DATABASE_URL` is empty or malformed. Make sure these are set in your **Web Service** variables (linked from PostgreSQL):

- `POSTGRES_USER` = `postgres` (default)
- `POSTGRES_PASSWORD` = [Railway generated password]
- `POSTGRES_HOST` = `postgres.railway.internal` (internal) or public URL
- `POSTGRES_PORT` = `5432`
- `POSTGRES_DB` = `railway` (default) or your database name

## Option 3: Railway Default Database Setup

Railway's PostgreSQL might use **peer authentication** or **trust authentication** for internal connections. In this case:

1. **Check Railway PostgreSQL logs** to see what authentication method is being used
2. Railway might auto-generate a password and store it in variables
3. Look for `POSTGRES_PASSWORD` in PostgreSQL service variables (not template, actual value)

## Quick Fix: Generate New Password

If Railway hasn't set a password:

1. **SSH into Railway PostgreSQL service** (if available):
   ```bash
   railway ssh --service [postgres-service-name]
   ```

2. **Or use Railway's PostgreSQL Query interface**:
   - Go to PostgreSQL service → **Query** tab
   - Run:
     ```sql
     ALTER USER postgres WITH PASSWORD 'your-secure-password';
     ```

3. **Then set this password** in Railway variables:
   - PostgreSQL service → Variables → `POSTGRES_PASSWORD`

## Verify Connection

After fixing credentials, verify the connection:

1. **Check Railway web service logs** for:
   - ✅ "Database engine created successfully"
   - ❌ No connection errors

2. **Test API endpoint**:
   ```bash
   curl https://your-railway-app.railway.app/api/markets
   ```
   Should return data or empty array, not 503 error.

## What I've Updated in Code

I've updated `src/config/settings.py` to:
- Handle empty username/password in `DATABASE_URL`
- Fall back to individual environment variables
- Use Railway defaults: `postgres` user, `railway` database
- Extract password from `POSTGRES_PASSWORD` or `PGPASSWORD` env vars

The code will now attempt to:
1. Use `DATABASE_URL` if valid
2. Fix empty credentials in `DATABASE_URL` using individual variables
3. Fall back to constructing URL from individual variables
4. Use defaults (postgres user, railway database) if variables are empty

## Next Steps

1. ✅ Set proper `POSTGRES_PASSWORD` in Railway PostgreSQL service
2. ✅ Link PostgreSQL variables to your Web Service
3. ✅ Update `DATABASE_URL` in Web Service to use template variables
4. ✅ Redeploy web service
5. ✅ Check logs for successful database connection


