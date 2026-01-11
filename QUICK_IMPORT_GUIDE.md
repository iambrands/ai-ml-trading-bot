# Quick Import Guide - Railway PostgreSQL

## Problem
Railway CLI needs a service linked before it can access variables automatically.

## Solution: Three Easy Methods

### Method 1: Use Railway Web Interface (Easiest) ✅

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on your **PostgreSQL service**
3. Click **"Connect"** or **"Query"** tab
4. Copy the entire contents of `local_db_backup_railway.sql`
5. Paste into the query editor
6. Click **"Run"** or press `Ctrl+Enter`

This is the simplest method - no CLI needed!

---

### Method 2: Link Service + Use Script

**Step 1: Link the PostgreSQL service**
```bash
railway service
```
Select **"Postgres"** when prompted.

**Step 2: Run the import script**
```bash
./import_to_railway_simple.sh
```

---

### Method 3: Manual psql Connection (Fastest)

**Step 1: Get DATABASE_URL from Railway Dashboard**

1. Go to Railway Dashboard
2. Click on your **PostgreSQL service**
3. Click **"Variables"** tab
4. Copy the **DATABASE_URL** value

**Step 2: Import using psql**
```bash
# Replace YOUR_DATABASE_URL with the actual URL from Railway
psql "YOUR_DATABASE_URL" -f local_db_backup_railway.sql
```

**Example:**
```bash
psql "postgresql://postgres:password@shuttle.proxy.rlwy.net:5432/railway" -f local_db_backup_railway.sql
```

**Step 3: Verify import**
```bash
psql "YOUR_DATABASE_URL" -c "SELECT COUNT(*) FROM markets;"
# Should show: 5
```

---

## Which Method Should I Use?

- **Method 1 (Web Interface)**: Use if you want the easiest, no-terminal approach
- **Method 2 (Script)**: Use if you've already linked the service
- **Method 3 (Manual psql)**: Use if you want the fastest, most direct approach

---

## Troubleshooting

### "No service linked"
Run `railway service` first and select "Postgres"

### "psql: error: could not connect to server"
- Check that your DATABASE_URL is correct
- Make sure Railway PostgreSQL service is running
- Verify network connectivity

### "password authentication failed"
- Verify the password in Railway Variables
- Check that you're using the correct DATABASE_URL
