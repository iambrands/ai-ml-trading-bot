# Step-by-Step: Link PostgreSQL to Web Service on Railway

Now that PostgreSQL is set up on Railway, follow these steps to link it to your web service.

## Step 1: Find Your PostgreSQL Service Name

1. **Go to Railway Dashboard** → Your project (handsome-perception)
2. **Look at your PostgreSQL service** - note the exact name (it might be "Postgres", "postgres", "PostgreSQL", or similar)
3. **Click on the PostgreSQL service** → "Variables" tab
4. **You'll see variables like**:
   - `PGHOST`
   - `PGPORT`
   - `PGDATABASE`
   - `PGUSER`
   - `PGPASSWORD`

**Note the exact service name** - you'll need it in Step 2.

## Step 2: Link PostgreSQL to Web Service

1. **Go to your `web` service** (not the PostgreSQL service)
2. **Click "Variables" tab**
3. **Click "+ New Variable"** (repeat for each of the 5 variables)

   Add these variables using Railway's reference syntax:

   | Variable Name | Value (replace `Postgres` with your actual service name) |
   |--------------|----------------------------------------------------------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **Important**: 
   - Replace `Postgres` with your actual PostgreSQL service name
   - If your service is named differently (e.g., "PostgreSQL" or "postgres-abc123"), use that instead
   - You can find the exact variable names by clicking on your PostgreSQL service → "Variables" tab
   - Railway's syntax is: `${{ServiceName.VARIABLE}}`

4. **Railway will automatically redeploy** your web service after adding variables

## Step 3: Verify Variables Are Set

After adding variables, you should see:
- All 5 variables listed in your web service's Variables tab
- Railway automatically redeploying your web service
- In deployment logs, you should see: "Database engine created successfully" (no more "[Errno 111] Connection refused")

## Step 4: Import Your Database Backup

Once variables are linked, import your backup:

### Option A: Using Railway CLI (Recommended)

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project (select your project)
railway link

# Connect to Railway PostgreSQL
railway connect postgres

# Once connected, import your SQL file:
# First, you need to upload the file or paste its contents
# If you have the file locally, use:
\i /path/to/local_db_backup_20260110_140827.sql

# Or if you can paste the SQL content, you can run it directly
```

### Option B: Using psql with Railway Connection String

1. **Get connection details from Railway**:
   - Go to PostgreSQL service → "Variables" tab
   - Copy the `DATABASE_URL` or individual connection details

2. **Import from your local machine**:
   ```bash
   # Using connection string (replace with actual values from Railway)
   psql "postgresql://USER:PASSWORD@HOST:PORT/DATABASE" -f local_db_backup_20260110_140827.sql
   ```

### Option C: Using Railway's Data Tab (If Available)

1. **Go to PostgreSQL service** → "Data" tab
2. **Use Railway's built-in SQL editor** to paste and run your SQL
3. **Copy contents of `local_db_backup_20260110_140827.sql`** and paste into SQL editor
4. **Click "Run"** or "Execute"

## Quick Import Commands

If you have Railway CLI set up and your PostgreSQL connection works:

```bash
# From your local machine, import directly
railway run --service postgres -- psql -d $DATABASE_URL -f local_db_backup_20260110_140827.sql

# Or connect and import interactively
railway connect postgres
# Then in PostgreSQL shell:
\i local_db_backup_20260110_140827.sql
```

## Verify Import Successful

After importing, verify your data:

```sql
-- Connect to Railway PostgreSQL
railway connect postgres

-- Check imported data
SELECT COUNT(*) FROM markets;  -- Should show 5
SELECT COUNT(*) FROM predictions;
SELECT COUNT(*) FROM signals;
SELECT COUNT(*) FROM trades;

-- View sample data
SELECT * FROM markets LIMIT 5;
```

## Troubleshooting

### Issue: "Variable not found" or "${{Postgres.PGHOST}} not resolved"

**Solution**: 
- Check your PostgreSQL service name in Railway
- The variable reference must match exactly
- Go to PostgreSQL service → Variables tab to see exact variable names
- Use the exact service name: `${{YourServiceName.PGHOST}}`

### Issue: Still seeing "[Errno 111] Connection refused"

**Solution**:
1. Verify all 5 variables are added to web service
2. Check variable names match exactly (case-sensitive)
3. Verify PostgreSQL service is running (green checkmark)
4. Check Railway deployment logs for any errors

### Issue: Can't connect to import data

**Solution**:
- Use Railway's web SQL editor (PostgreSQL service → Data tab)
- Or upload SQL file through Railway's interface
- Or use Railway CLI: `railway connect postgres`

