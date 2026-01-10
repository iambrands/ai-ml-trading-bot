# Import Database to Railway PostgreSQL

This guide will help you import your local database backup into Railway's PostgreSQL instance.

## Prerequisites

✅ PostgreSQL service is set up on Railway  
✅ PostgreSQL service variables are linked to your web service  
✅ Database backup file exists: `local_db_backup_railway.sql`

## Step 1: Get Railway PostgreSQL Connection Details

Railway provides connection details through environment variables. Your web service should have these linked:
- `DATABASE_URL` - Full connection string (used by the app)
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Individual variables

## Step 2: Connect to Railway PostgreSQL

You have two options:

### Option A: Using Railway CLI (Recommended)

1. **Install Railway CLI** (if not already installed):
   ```bash
   brew install railway
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link to your project**:
   ```bash
   railway link
   ```
   Select your project when prompted.

4. **Get PostgreSQL connection string**:
   ```bash
   railway variables
   ```
   Look for `DATABASE_URL` or use individual variables.

5. **Connect to PostgreSQL**:
   ```bash
   railway connect postgres
   ```
   This opens a PostgreSQL shell connected to your Railway database.

### Option B: Using psql with Connection String

1. **Get the connection string from Railway dashboard**:
   - Go to your PostgreSQL service in Railway
   - Click on "Variables" tab
   - Copy the `DATABASE_URL` value (it will look like: `postgresql://postgres:password@host:port/database`)

2. **Connect using psql**:
   ```bash
   psql "YOUR_DATABASE_URL_HERE"
   ```
   Replace `YOUR_DATABASE_URL_HERE` with the actual connection string.

## Step 3: Import the Database

Once connected to Railway PostgreSQL, you can import your database:

### Using Railway CLI (Option A):

1. **Exit the PostgreSQL shell** (if you used `railway connect postgres`):
   ```sql
   \q
   ```

2. **Import the database**:
   ```bash
   railway run psql < local_db_backup_railway.sql
   ```
   Or:
   ```bash
   cat local_db_backup_railway.sql | railway run psql
   ```

### Using psql directly (Option B):

```bash
psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
```

Or if you're already in the psql shell:
```sql
\i /path/to/local_db_backup_railway.sql
```

## Step 4: Verify Import

After importing, verify the data:

```sql
-- Check tables
\dt

-- Check row counts
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

-- Check a sample of data
SELECT * FROM markets LIMIT 5;
SELECT * FROM predictions LIMIT 5;
```

Expected results:
- **markets**: 5 rows
- **predictions**: 13 rows
- **signals**: 13 rows
- **trades**: 13 rows
- **portfolio_snapshots**: 1 row

## Step 5: Update Your Web Service

After importing, your Railway web service should automatically connect to the database using the `DATABASE_URL` environment variable that's already linked.

## Troubleshooting

### Error: "role 'root' does not exist"
- This is normal - Railway's health checks may use 'root', but your app uses the `DATABASE_URL` with the correct user.
- Your app should work fine with `DATABASE_URL` variable.

### Error: "permission denied"
- Make sure you're using the correct `DATABASE_URL` from Railway.
- Verify the PostgreSQL service variables are properly linked to your web service.

### Error: "database does not exist"
- Check that `POSTGRES_DB` or `PGDATABASE` matches your database name.
- Railway may have created a default database - check the variables.

### Import fails with ownership errors
- The `local_db_backup_railway.sql` file has been pre-processed to use `postgres` as the owner instead of `iabadvisors`.
- If you still see errors, you can manually fix them:
  ```sql
  ALTER TABLE public.markets OWNER TO postgres;
  -- Repeat for other tables
  ```

## Next Steps

1. ✅ Database imported successfully
2. ✅ Verify data in Railway dashboard or via CLI
3. ✅ Test your web service - it should now read from Railway PostgreSQL
4. ✅ Check Railway logs to ensure no connection errors

## Notes

- The `local_db_backup_railway.sql` file has been modified to use `postgres` as the owner (Railway's default PostgreSQL user) instead of `iabadvisors`.
- All sequences, indexes, and constraints have been updated accordingly.
- Your trained models (`.pkl` files) are already in git and will be available in Railway after deployment.

