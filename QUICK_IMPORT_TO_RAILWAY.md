# Quick Guide: Import Database to Railway

You've successfully exported your local database! Now let's import it to Railway PostgreSQL.

## Step 1: Set Up Railway PostgreSQL (If Not Done Yet)

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Select your project** (handsome-perception)
3. **Click "+ New"** → **"Database"** → **"Add PostgreSQL"**
4. **Wait for provisioning** (1-2 minutes)
5. **Note**: Railway will create a new PostgreSQL service

## Step 2: Link PostgreSQL to Web Service

1. **Go to your `web` service** in Railway
2. **Click "Variables" tab**
3. **Add these 5 variables** (using Railway's `${{Service.Variable}}` syntax):

   Click **"+ New Variable"** for each:

   | Variable Name | Value |
   |--------------|-------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **Important**: 
   - Replace `Postgres` with the actual name of your PostgreSQL service in Railway
   - Railway will show you the exact variable names when you click on your PostgreSQL service → "Variables" tab
   - The syntax is `${{ServiceName.VARIABLE}}`

4. **Railway will automatically redeploy** your web service after adding variables

## Step 3: Import Your Database Data

### Option A: Using Railway CLI (Recommended)

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Get connection details
railway variables --service postgres

# Import using pg_restore (using Railway connection)
# First, get the connection details from Railway PostgreSQL service → Variables tab
# Then run:
pg_restore \
  -h ${{Postgres.PGHOST}} \
  -U ${{Postgres.PGUSER}} \
  -d ${{Postgres.PGDATABASE}} \
  -F c \
  local_db_backup_20260110_140827.dump
```

### Option B: Using Railway's Web Terminal

1. **Go to Railway Dashboard** → Your **PostgreSQL service**
2. **Click "Data" tab** (if available)
3. **Or go to "Deployments"** → **"Latest"** → **"View Terminal"**
4. **Upload and import the SQL file**:
   ```bash
   # Upload the .sql file first (Railway web interface may have upload option)
   # Then run:
   psql $DATABASE_URL -f local_db_backup_20260110_140827.sql
   ```

### Option C: Using psql with Connection String

1. **Get connection string from Railway**:
   - Go to PostgreSQL service → "Variables" tab
   - Find `DATABASE_URL` or construct from individual variables
   - Format: `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`

2. **Import using psql**:
   ```bash
   # Using connection string
   psql "postgresql://postgres:PASSWORD@HOST:PORT/railway" -f local_db_backup_20260110_140827.sql
   
   # Or using individual variables
   psql -h HOST -U postgres -d railway -f local_db_backup_20260110_140827.sql
   ```

### Option D: Using Railway Connect (Simplest)

```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Once connected, you can run SQL commands:
\i local_db_backup_20260110_140827.sql

# Or restore from dump:
# (Exit PostgreSQL shell first: \q)
pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} local_db_backup_20260110_140827.dump
```

## Step 4: Verify Import

After importing, verify your data:

```sql
-- Connect to Railway PostgreSQL
railway connect postgres

-- Check imported data
SELECT COUNT(*) FROM markets;  -- Should show 5
SELECT COUNT(*) FROM predictions;
SELECT COUNT(*) FROM signals;
SELECT COUNT(*) FROM trades;
SELECT COUNT(*) FROM portfolio_snapshots;

-- View sample data
SELECT * FROM markets LIMIT 5;
```

## Troubleshooting

### Issue: "Service 'Postgres' not found"

**Solution**: 
- Check the exact name of your PostgreSQL service in Railway
- The variable reference should match: `${{YourPostgresServiceName.PGHOST}}`
- You can see available variables by going to PostgreSQL service → Variables tab

### Issue: "Connection refused" or "could not connect"

**Solution**:
1. Make sure PostgreSQL service is running (green checkmark)
2. Verify you've added all 5 variables to web service
3. Check variable names match exactly (case-sensitive)
4. Make sure variables use Railway's reference syntax: `${{ServiceName.VARIABLE}}`

### Issue: "Table already exists"

**Solution**:
- The app auto-creates tables on startup
- If you import before tables are created, let the app create them first
- Then import data, or drop tables first and let app recreate them

### Issue: Foreign key constraint violations

**Solution**:
- Export/import all tables at once (which you did)
- Or import in order: markets → predictions → signals → trades

## Quick Command Reference

```bash
# Check Railway services
railway status

# View PostgreSQL variables
railway variables --service postgres

# Connect to PostgreSQL
railway connect postgres

# Import from SQL file (after connecting)
\i local_db_backup_20260110_140827.sql

# Or restore from dump (from local terminal)
pg_restore -h HOST -U postgres -d railway -F c local_db_backup_20260110_140827.dump
```

## After Import - Verify Everything Works

1. **Check Railway deployment logs**:
   - Should see: "Database engine created successfully"
   - Should see: "Database tables initialized successfully"
   - Should NOT see: "[Errno 111] Connection refused"

2. **Test API endpoints**:
   - `https://web-production-c490dd.up.railway.app/health`
   - `https://web-production-c490dd.up.railway.app/predictions?limit=10`
   - `https://web-production-c490dd.up.railway.app/signals?limit=10`
   - Should return your data (not empty lists)

3. **Check models are loaded**:
   - Models should be in Railway deployment (from git)
   - Check logs for any model loading errors
   - Test prediction generation

---

**Your backup files are ready**:
- `local_db_backup_20260110_140827.dump` (25KB)
- `local_db_backup_20260110_140827.sql` (25KB)

Once you set up Railway PostgreSQL and import these files, all your data and models will be on Railway! 🚀



