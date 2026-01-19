# Whale Discovery Setup Guide

## Quick Start

Whale discovery uses the **Polymarket subgraph** (GraphQL API), not Alchemy. The Alchemy API key is optional for future Web3 integration.

### Step 1: Set Alchemy API Key (Optional)

```bash
# Set Alchemy API key in Railway (optional, for future Web3 features)
railway variables set ALCHEMY_API_KEY=QC9BcNYIzvefC4dQJ_qKI

# Verify it's set
railway variables | grep ALCHEMY
```

### Step 2: Run Whale Discovery

```bash
# Run whale discovery initialization
railway run python scripts/init_whale_discovery.py
```

**Expected Output:**
```
======================================================================
  WHALE DISCOVERY INITIALIZATION
======================================================================

✅ Database URL configured
⚠️  ALCHEMY_API_KEY not set (optional, for future Web3 integration)
   Note: WhaleTracker uses Polymarket subgraph, not Alchemy

----------------------------------------------------------------------
STEP 1: Discovering Top Whales
----------------------------------------------------------------------
🐋 Connecting to Polymarket subgraph...
   This may take 30-60 seconds...

✅ Discovered 250 whale wallets

----------------------------------------------------------------------
STEP 2: Indexing Whales in Database
----------------------------------------------------------------------
💾 Indexing whales in database...
✅ Indexed 250 whales

======================================================================
  INITIALIZATION COMPLETED SUCCESSFULLY
======================================================================

✅ Discovered: 250 whales
✅ Indexed: 250 whales
```

### Step 3: Test Alchemy Connection (Optional)

```bash
# Test Alchemy API connection (for future Web3 integration)
railway run python scripts/test_alchemy.py
```

### Step 4: Verify Whale Data

```bash
# Test API endpoint
curl https://web-production-c490dd.up.railway.app/whales/leaderboard?limit=10

# Should return JSON with 10 whales
```

### Step 5: Run Diagnostics

```bash
# Verify everything is working
railway run python scripts/diagnose_issues.py
```

## How Whale Discovery Works

**Current Implementation:**
- Uses **Polymarket GraphQL Subgraph**: `https://api.thegraph.com/subgraphs/name/polymarket/matic-markets`
- Queries top 500 traders by `volumeTraded`
- Filters for wallets with > $10k volume
- Stores in `whale_wallets` table

**Future (Optional):**
- Alchemy API can be used for direct blockchain queries
- Web3 integration for real-time transaction monitoring
- On-chain data for enhanced whale tracking

## Troubleshooting

### No Whales Discovered

**Possible causes:**
1. Polymarket subgraph is down or slow
2. Network timeout
3. Query format changed

**Solutions:**
```bash
# Check Railway logs
railway logs --tail 100 | grep -i whale

# Try again after a few minutes
railway run python scripts/init_whale_discovery.py
```

### Database Connection Error

```bash
# Verify DATABASE_URL is set
railway variables | grep DATABASE_URL

# Test connection
railway run python -c "import os; from src.database.connection import AsyncSessionLocal; print('DB OK')"
```

### Alchemy Connection Fails (Optional)

If testing Alchemy (not required for whale discovery):

```bash
# Check if Web3 is installed
railway run python -c "from web3 import Web3; print('Web3 OK')"

# Install if missing (add to requirements.txt)
pip install web3

# Test connection
railway run python scripts/test_alchemy.py
```

## Expected Results

After running initialization:

1. ✅ **250-500 whales** discovered from Polymarket subgraph
2. ✅ **Whales indexed** in `whale_wallets` table
3. ✅ **Whale leaderboard** shows data at `/whales/leaderboard`
4. ✅ **Frontend** displays whales in "🐋 Whale Tracker" tab
5. ✅ **Diagnostics** show: `✓ Whale Wallets: 250 records`

## API Endpoints

After initialization, these endpoints should work:

- `GET /whales/leaderboard?limit=50` - Returns top whales
- `GET /whales/recent-activity?hours=24` - Returns recent whale trades
- `GET /whales/alerts?unread_only=true` - Returns whale alerts

## Next Steps

1. **Monitor Recent Trades** (optional):
   ```python
   # Call monitor_whale_trades() periodically
   tracker.monitor_whale_trades(hours=24)
   ```

2. **Set Up Alerts** (optional):
   - Configure Discord/Slack webhooks
   - Get notified on large whale trades

3. **View in Dashboard**:
   - Navigate to "🐋 Whale Tracker" tab
   - See leaderboard, recent activity, and alerts

