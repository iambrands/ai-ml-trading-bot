# Linking Railway PostgreSQL to Web Service - Step by Step

You have PostgreSQL set up on Railway! Now let's link it to your web service.

## Step 1: Find Your PostgreSQL Service Name

1. **Go to Railway Dashboard** → Your project (handsome-perception)
2. **Look at your services list** - you should see:
   - `web` (your web service)
   - `Postgres` or `postgres` or similar (your PostgreSQL service)
3. **Note the EXACT name** of your PostgreSQL service (case-sensitive!)
   - It might be: `Postgres`, `postgres`, `PostgreSQL`, or something else

## Step 2: Add Variables to Your Web Service

1. **Go to your `web` service** (not the PostgreSQL service)
2. **Click "Variables" tab**
3. **Click "+ New Variable"** and add these 5 variables:

   **Important**: Replace `Postgres` with your actual PostgreSQL service name!

   | Variable Name | Value |
   |--------------|-------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **How to know the service name**:
   - Look at your services list in Railway
   - The PostgreSQL service will show as something like "Postgres", "postgres", etc.
   - Use that exact name in the variable value
   - Example: If service is named `postgres`, use `${{postgres.PGHOST}}`

4. **After adding all 5 variables**, Railway will automatically redeploy your web service

## Step 3: Verify Connection

1. **Check deployment logs** for your web service
2. **Look for**: "Database engine created successfully"
3. **Should NOT see**: "[Errno 111] Connection refused" errors anymore

## Step 4: Import Your Database Backup

Once linked, import your data:

### Option 1: Using Railway CLI (Recommended)

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Connect to PostgreSQL
railway connect postgres

# Once connected, you can import:
# Method A: Copy and paste SQL content directly
# (Open local_db_backup_20260110_140827.sql and paste contents)

# Method B: If Railway allows file upload:
\i /path/to/local_db_backup_20260110_140827.sql
```

### Option 2: Using Railway's Web Interface (Easiest)

1. **Go to PostgreSQL service** → Click on it
2. **Look for "Data" tab or "Connect" tab**
3. **If there's a SQL editor**:
   - Open `local_db_backup_20260110_140827.sql` on your local machine
   - Copy all contents (707 lines)
   - Paste into Railway's SQL editor
   - Click "Run" or "Execute"

### Option 3: Using DATABASE_URL Directly

Since Railway provides `DATABASE_URL`, you can use it directly:

```bash
# Get DATABASE_URL from PostgreSQL service → Variables tab
# Then import from your local machine:

psql "$DATABASE_URL" -f local_db_backup_20260110_140827.sql
```

Or if you have Railway CLI:

```bash
# Export DATABASE_URL to your environment
railway variables --service postgres

# Then import
railway run --service postgres psql "$DATABASE_URL" -f local_db_backup_20260110_140827.sql
```

## Quick Commands

```bash
# 1. Connect to Railway PostgreSQL
railway connect postgres

# 2. In PostgreSQL shell, check if tables exist
\dt

# 3. Import SQL file (if you can upload it or paste contents)
\i local_db_backup_20260110_140827.sql

# Or paste SQL content directly into Railway's SQL editor
```

## Troubleshooting

### Issue: Variable Reference Not Working

**Solution**: 
- Make sure you use the EXACT service name
- Check your PostgreSQL service name in Railway dashboard
- Variable syntax is: `${{ServiceName.VARIABLE}}`
- Case-sensitive! If service is `postgres`, use `${{postgres.PGHOST}}`, not `${{Postgres.PGHOST}}`

### Issue: Can't Import via CLI

**Solution**: Use Railway's web SQL editor instead:
- Go to PostgreSQL service → Look for "Data" or "Connect" tab
- Use the SQL editor to paste and run your SQL
- This is often easier than CLI for one-time imports

### Issue: Tables Already Exist

**Solution**: 
- The app auto-creates tables on startup
- If you import before tables exist, the import will create them
- If tables already exist, the import will add data (or error if duplicates)
- You can drop tables first if needed: `DROP TABLE IF EXISTS markets CASCADE;`


