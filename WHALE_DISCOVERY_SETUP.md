# Whale Discovery Setup Guide

This guide explains how to run the whale discovery script to populate the Whale Tracker with top Polymarket traders.

## Understanding the Problem

When you run `railway run python scripts/init_whale_discovery.py`, the script runs **locally on your computer** but tries to connect to Railway's database using an internal hostname (`postgres.railway.internal`). This hostname is only accessible from within Railway's network, not from your local machine.

## Solution: Create a Database Tunnel

A "tunnel" creates a secure connection that makes Railway's internal database accessible from your local machine.

---

## Step-by-Step Instructions

### Method 1: Using Railway Tunnel (Recommended)

#### Step 1: Create the Database Tunnel

Open your terminal and run:

```bash
railway connect postgres
```

**What happens:**
- Railway creates a secure tunnel to your database
- Your terminal will show connection details
- A `psql` prompt will open (PostgreSQL command-line interface)

**You'll see something like:**
```
Connecting to postgres.railway.internal:5432...
Connected to Railway PostgreSQL
psql (14.x)
Type "help" for help.

railway=>
```

#### Step 2: Exit the psql Prompt

You don't need to use `psql` right now. Simply type:

```sql
\q
```

Then press Enter. This exits `psql` but **keeps the tunnel active** in the background.

**Important:** Keep this terminal window open! The tunnel stays active as long as this terminal session is running.

#### Step 3: Open a NEW Terminal Window

**Why?** The tunnel is running in the first terminal. You need a second terminal to run your script.

1. Open a new terminal window/tab
2. Navigate to your project directory:
   ```bash
   cd /Users/iabadvisors/ai-ml-trading-bot
   ```

#### Step 4: Set the Tunneled Database URL

The tunnel creates a local connection. You need to tell the script to use it:

```bash
# Get the tunneled connection string from Railway
# It will look like: postgresql://postgres:password@localhost:5432/railway

# Set it as an environment variable
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/railway"
```

**How to get the exact connection string:**
- Look at the first terminal window where you ran `railway connect postgres`
- Railway usually displays the connection string
- Or check Railway Dashboard > Postgres > Connect > Connection String

#### Step 5: Run the Whale Discovery Script

Now run the script in your new terminal:

```bash
python scripts/init_whale_discovery.py
```

**Expected output:**
```
======================================================================
  WHALE DISCOVERY INITIALIZATION
  Discovering and indexing top Polymarket traders
======================================================================

✅ Database URL configured
   Host: localhost:5432/railway

STEP 1: Discovering Top Whales
----------------------------------------------------------------------
🐋 Discovering top whales from Polymarket...
✅ Discovered 100 whales

STEP 2: Indexing Whales in Database
----------------------------------------------------------------------
💾 Indexing 100 whales in database...
✅ Connected to database
   Indexed 10/100 whales...
   Indexed 20/100 whales...
   ...
✅ Indexed 100 whales successfully

STEP 3: Verification
----------------------------------------------------------------------
🔍 Verifying whale data...

   Total active whales: 100
   Recent trades (24h): 0

   Top 5 Whales:
   #1: $500,000 volume, 75.0% win rate, $25,000 P&L
        0x12345678...12345678
   ...
```

#### Step 6: Close the Tunnel (When Done)

When you're finished, go back to the first terminal window and press `Ctrl+C` to close the tunnel.

---

### Method 2: Run Directly on Railway (Alternative)

If the tunnel method is too complex, you can run the script directly on Railway's infrastructure:

#### Option A: Via Railway CLI

```bash
# This runs the script on Railway's servers (not locally)
railway run python scripts/init_whale_discovery.py
```

**Note:** This might still have connection issues. If it does, use Method 1.

#### Option B: Create a Railway Task/Job

1. Go to Railway Dashboard
2. Create a new service or use an existing one
3. Add a one-off command: `python scripts/init_whale_discovery.py`
4. Run it from the dashboard

---

## Troubleshooting

### Error: "nodename nor servname provided, or not known"

**Cause:** The script is trying to connect to `postgres.railway.internal` from your local machine.

**Solution:** Use Method 1 (create a tunnel) or ensure you're using the tunneled `DATABASE_URL` with `localhost` instead of `postgres.railway.internal`.

### Error: "Connection refused" or "Can't connect to localhost:5432"

**Cause:** The tunnel isn't active or you're using the wrong port.

**Solution:**
1. Make sure `railway connect postgres` is still running in another terminal
2. Check what port Railway assigned to the tunnel (it might not be 5432)
3. Update your `DATABASE_URL` with the correct port

### Error: "No module named 'src'"

**Cause:** You're not in the project directory or Python path is wrong.

**Solution:**
```bash
cd /Users/iabadvisors/ai-ml-trading-bot
python scripts/init_whale_discovery.py
```

### Tunnel Closes Unexpectedly

**Cause:** Network interruption or Railway session timeout.

**Solution:** Run `railway connect postgres` again to recreate the tunnel.

---

## Quick Reference

**Create tunnel:**
```bash
railway connect postgres
# Then type \q to exit psql (keeps tunnel active)
```

**In a NEW terminal, run script:**
```bash
cd /Users/iabadvisors/ai-ml-trading-bot
export DATABASE_URL="postgresql://postgres:PASSWORD@localhost:PORT/railway"
python scripts/init_whale_discovery.py
```

**Close tunnel:**
- Go to the terminal running the tunnel
- Press `Ctrl+C`

---

## Verification

After running the script successfully, verify the data:

1. **Check the API:**
   ```bash
   curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=5
   ```

2. **View in UI:**
   - Go to: https://web-production-c490dd.up.railway.app
   - Click "🐋 Whale Tracker" in the left sidebar
   - You should see the leaderboard populated

3. **Check database directly:**
   ```bash
   railway connect postgres
   # Then in psql:
   SELECT COUNT(*) FROM whale_wallets WHERE is_active = true;
   SELECT rank, wallet_address, total_volume FROM whale_wallets ORDER BY rank LIMIT 5;
   \q
   ```

---

## Next Steps

Once whales are indexed:
- The Whale Tracker UI will automatically display them
- The leaderboard will update every 60 seconds
- You can monitor whale activity in real-time

For more information, see:
- `WHALE_CALENDAR_INITIALIZATION.md` - Full initialization guide
- `RUN_DIAGNOSTIC.md` - Troubleshooting guide
