# Getting Railway DATABASE_URL for SQL Import

## The Issue
The "Connect to Postgres" modal shows a **template variable** (`${{ Postgres.DATABASE_URL }}`), but for importing SQL files with `psql`, you need the **actual resolved DATABASE_URL value**.

## Solution: Get the Actual DATABASE_URL

### Method 1: From Variables Tab (Recommended) ✅

1. In Railway Dashboard, click on your **PostgreSQL service** ("Postgres")
2. Click the **"Variables"** tab (not "Connect")
3. Look for **`DATABASE_URL`** in the list of variables
4. Click on it or copy the full value
5. It should look like: `postgresql://postgres:password@host:port/database`

**Example:**
```
postgresql://postgres:abc123xyz@shuttle.proxy.rlwy.net:5432/railway
```

### Method 2: Check Public Network Tab

1. In the "Connect to Postgres" modal
2. Click the **"Public Network"** tab (instead of "Private Network")
3. Look for a connection string shown there
4. Copy that connection string

### Method 3: From Web Service Variables

If your web service has the DATABASE_URL linked:

1. Go to your **web service** (not PostgreSQL)
2. Click **"Variables"** tab
3. Look for **`DATABASE_URL`** 
4. The value should be the resolved connection string

---

## Using the DATABASE_URL

Once you have the actual DATABASE_URL, use it with `psql`:

```bash
# Replace with your actual DATABASE_URL
psql "postgresql://postgres:password@host:port/database" -f local_db_backup_railway.sql
```

**Example:**
```bash
psql "postgresql://postgres:abc123xyz@shuttle.proxy.rlwy.net:5432/railway" -f local_db_backup_railway.sql
```

---

## Alternative: Use Railway Web Query Interface

If Railway provides a query interface:

1. In PostgreSQL service, look for **"Query"** or **"SQL"** tab
2. Open the query editor
3. Copy the entire contents of `local_db_backup_railway.sql`
4. Paste into the editor
5. Click **"Run"** or press `Ctrl+Enter`

This method doesn't require the DATABASE_URL at all!

---

## Troubleshooting

### "Template variable shown instead of actual value"
- The `${{ Postgres.DATABASE_URL }}` is a template for linking services
- You need to find the actual resolved value in Variables tab

### "DATABASE_URL not in Variables tab"
- Check if you're looking at the PostgreSQL service (not web service)
- The variable might be named differently
- Check "Public Network" tab in Connect modal

### "Connection refused"
- Verify the DATABASE_URL is correct
- Make sure PostgreSQL service is "Online"
- Check if you need to use Public Network connection string


