# Migrating Local PostgreSQL Data to Railway

This guide explains how to migrate your existing local PostgreSQL data to Railway's PostgreSQL service.

## Important: Separate Database Instances

**Railway PostgreSQL is a completely separate database instance** - it will NOT automatically connect to your local database. You need to export your local data and import it into Railway.

## Option 1: Export and Import Data (Recommended)

### Step 1: Export Data from Local Database

On your local machine, export your database:

```bash
# Export entire database (all tables and data)
pg_dump -h localhost -U iabadvisors -d polymarket_trader -F c -f local_db_backup.dump

# Or export as SQL script (more portable)
pg_dump -h localhost -U iabadvisors -d polymarket_trader -F p -f local_db_backup.sql

# Or export specific tables only
pg_dump -h localhost -U iabadvisors -d polymarket_trader -t markets -t predictions -t signals -F p -f specific_tables.sql
```

**Note**: Replace `iabadvisors` with your actual PostgreSQL username if different.

### Step 2: Get Railway Database Connection Details

1. **Go to Railway Dashboard** → Your PostgreSQL service
2. **Click on "Variables" tab** to see connection details, OR
3. **Click on "Connect" tab** to see connection string

You'll see something like:
- Host: `containers-us-west-xxx.railway.app`
- Port: `5432` (usually)
- Database: `railway`
- User: `postgres`
- Password: `[automatically generated]`

### Step 3: Import Data to Railway PostgreSQL

**Option A: Using Railway CLI (Recommended)**

```bash
# Install Railway CLI if you haven't
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Set up Railway PostgreSQL first (see RAILWAY_POSTGRESQL_SETUP.md)

# Connect to Railway PostgreSQL
railway connect postgres

# In the PostgreSQL shell, run:
\i local_db_backup.sql

# Or restore from dump file
pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} local_db_backup.dump
```

**Option B: Using psql directly with Railway connection string**

```bash
# Get connection string from Railway PostgreSQL service → Variables tab
# Or use Railway's connection details

# Import SQL file
psql "postgresql://postgres:PASSWORD@HOST:PORT/railway" -f local_db_backup.sql

# Or restore from dump
pg_restore -h HOST -U postgres -d railway -f local_db_backup.dump
```

**Option C: Using Railway's Web Interface**

1. Go to Railway PostgreSQL service
2. Click "Data" tab
3. Use Railway's built-in SQL editor to run queries
4. Paste and execute your exported SQL

**Option D: Using a database client (pgAdmin, DBeaver, etc.)**

1. Get connection details from Railway PostgreSQL service
2. Connect using a database client
3. Import/restore your backup file

## Option 2: Re-run Data Collection (If You Prefer Fresh Start)

If you don't need your existing data, or it's easier to regenerate:

1. **Set up Railway PostgreSQL** (see RAILWAY_POSTGRESQL_SETUP.md)
2. **The database schema will auto-initialize** when your app starts
3. **Re-run your data collection scripts**:
   ```bash
   # Run on Railway (or locally and let app sync)
   railway run python scripts/generate_predictions.py
   ```

This will start fresh with new data collected from APIs.

## Option 3: Hybrid Approach (Export Important Data Only)

If you only want to migrate specific important data:

```bash
# Export only specific tables
pg_dump -h localhost -U iabadvisors -d polymarket_trader \
  -t markets \
  -t predictions \
  -t model_performance \
  -F p -f important_data.sql

# Then import to Railway PostgreSQL
railway connect postgres
\i important_data.sql
```

## Option 4: Sync Data Periodically (For Development)

If you want to keep local and Railway in sync during development:

1. **Set up both databases** (local + Railway)
2. **Use environment variables to switch between them**
3. **Periodically export from local and import to Railway**:
   ```bash
   # Automated sync script
   ./scripts/sync_to_railway.sh
   ```

## Checking What Data You Have Locally

Before migrating, check what data you have:

```bash
# Connect to local database
psql -h localhost -U iabadvisors -d polymarket_trader

# Check table counts
SELECT 
  'markets' as table_name, COUNT(*) as row_count FROM markets
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'trades', COUNT(*) FROM trades
UNION ALL
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots;

# Check latest data
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;
SELECT * FROM markets ORDER BY created_at DESC LIMIT 10;
```

## Important Considerations

### 1. **Schema Differences**
- Railway PostgreSQL will use the schema from `src/database/models.py`
- Make sure your local schema matches, or update the migration script
- The app auto-creates tables on startup using SQLAlchemy models

### 2. **Data Volume**
- If you have a lot of data, export/import may take time
- Consider exporting only recent/relevant data
- Training data (`feature_snapshots`) can be large - you may want to regenerate this

### 3. **Foreign Key Constraints**
- Make sure to export tables in the correct order (parent tables before child tables)
- Or export all at once and let PostgreSQL handle dependencies

### 4. **Date/Time Considerations**
- Verify timezone handling matches between local and Railway
- The app uses UTC by default (`datetime.now(timezone.utc)`)

### 5. **Model Training Data**
- If you have trained models locally, those are in `data/models/*.pkl` files
- Models are NOT stored in the database, so copy `.pkl` files separately if needed
- Training data (`feature_snapshots`) can be regenerated from resolved markets

## Quick Migration Checklist

- [ ] Check what data you have locally
- [ ] Export local database using `pg_dump`
- [ ] Set up Railway PostgreSQL service
- [ ] Link PostgreSQL to web service in Railway
- [ ] Import exported data to Railway PostgreSQL
- [ ] Verify data imported correctly
- [ ] Check Railway deployment logs for database connection
- [ ] Test API endpoints to verify data is accessible
- [ ] (Optional) Copy model files (`data/models/*.pkl`) if needed

## Alternative: Keep Local Database for Development

You don't have to migrate everything! Consider:

1. **Use Railway PostgreSQL for production** (Railway deployment)
2. **Keep local PostgreSQL for development** (local testing)
3. **Use environment variables to switch between them**

This way you can:
- Develop and test locally with your existing data
- Deploy to Railway with fresh or specific data
- Keep environments separate

## Troubleshooting

### Issue: "Permission denied" when importing

**Solution**: Make sure you're using the correct Railway PostgreSQL credentials. Check the Variables tab in Railway.

### Issue: "Table already exists" errors

**Solution**: The app auto-creates tables. Drop existing tables first if needed:
```sql
DROP TABLE IF EXISTS portfolio_snapshots CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS feature_snapshots CASCADE;
DROP TABLE IF EXISTS model_performance CASCADE;
DROP TABLE IF EXISTS markets CASCADE;
```

Then let the app recreate them, or import your data.

### Issue: Foreign key constraint violations

**Solution**: Export/import tables in the correct order, or export everything at once.

### Issue: Large export files

**Solution**: 
- Use compressed format: `pg_dump -F c` (custom format)
- Export only specific tables
- Consider filtering by date: `WHERE created_at > '2024-01-01'`

---

## Quick Command Summary

```bash
# Export from local
pg_dump -h localhost -U iabadvisors -d polymarket_trader -F c -f backup.dump

# Import to Railway (after setting up Railway PostgreSQL)
railway connect postgres
pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} backup.dump

# Or use Railway CLI to run restore
railway run pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} backup.dump
```


