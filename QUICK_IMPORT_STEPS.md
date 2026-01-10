# Quick Database Import Steps

## ✅ Prerequisites Completed

- ✅ Railway CLI installed
- ✅ Logged in to Railway  
- ✅ Project "handsome-perception" linked
- ✅ SQL file ready: `local_db_backup_railway.sql` (707 lines, all owners set to `postgres`)

## 🚀 Import Database (Choose One Method)

### Method 1: Using the Import Script (Easiest)

1. **Get your DATABASE_URL from Railway Dashboard:**
   - Go to: https://railway.app
   - Select project: **handsome-perception**
   - Click on your **PostgreSQL service** (should be named "Postgres" or similar)
   - Click **"Variables"** tab
   - Copy the **`DATABASE_URL`** value
     - It looks like: `postgresql://postgres:password@host:port/database`

2. **Run the import script:**
   ```bash
   ./import_to_railway.sh "YOUR_DATABASE_URL_HERE"
   ```
   Replace `YOUR_DATABASE_URL_HERE` with the actual DATABASE_URL from Railway.

   The script will:
   - Import all tables and data
   - Verify the import (show row counts)
   - Display success message

### Method 2: Manual Import

1. **Get DATABASE_URL** (same as Method 1)

2. **Import directly:**
   ```bash
   psql "YOUR_DATABASE_URL_HERE" < local_db_backup_railway.sql
   ```

3. **Verify import:**
   ```bash
   psql "YOUR_DATABASE_URL_HERE" -c "SELECT COUNT(*) FROM markets;"
   ```
   Should show: `5` (markets)

### Method 3: Using Railway CLI (If you can select service interactively)

**Run this in your own terminal** (interactive):

```bash
# Link to PostgreSQL service (will prompt for selection)
railway service link

# Import database
railway run psql < local_db_backup_railway.sql
```

## 📊 Expected Results After Import

After successful import, you should see:

- ✅ **markets**: 5 rows
- ✅ **predictions**: 13 rows
- ✅ **signals**: 13 rows  
- ✅ **trades**: 13 rows
- ✅ **portfolio_snapshots**: 1 row

## 🔍 Verify Your Web Service

After importing:

1. **Your Railway web service should automatically connect** using the `DATABASE_URL` variable
2. **Check Railway logs** to confirm no database connection errors
3. **Test your API endpoints:**
   - `/api/markets` - Should show 5 markets
   - `/api/predictions` - Should show 13 predictions
   - `/api/signals` - Should show 13 signals
   - `/api/trades` - Should show 13 trades

## ⚠️ Troubleshooting

### "psql: command not found"
```bash
# Install PostgreSQL client (macOS)
brew install postgresql
```

### "permission denied" or "role does not exist"
- ✅ The SQL file has been pre-processed to use `postgres` as owner
- Make sure you're using the correct `DATABASE_URL` from Railway
- Railway's default PostgreSQL user is `postgres`

### "database does not exist"
- Check that your `DATABASE_URL` points to the correct database name
- Railway may have created a default database - check variables in dashboard

### Connection timeout
- Ensure Railway PostgreSQL service is running (check Railway dashboard)
- Verify the `DATABASE_URL` host is correct (should use `RAILWAY_PRIVATE_DOMAIN` for internal connections)

## 📝 Notes

- The `local_db_backup_railway.sql` file has been modified:
  - All `OWNER TO iabadvisors` → `OWNER TO postgres`
  - Compatible with Railway's default PostgreSQL user
- Your web service is already configured to use `DATABASE_URL` from environment
- No code changes needed - it will automatically connect once database is imported

