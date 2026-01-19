# Whale Tracker & Economic Calendar - Initialization Guide

## Issues Fixed ✅

1. **JavaScript Errors Fixed**:
   - Added null checks in `showTab()` function to prevent `classList` errors
   - Added null checks in all auto-refresh intervals
   - Added data validation (Array.isArray) before displaying
   - Added console logging for debugging API responses

2. **Missing Calendar Tab HTML**:
   - Added the missing `<div id="calendar" class="tab-content">` section
   - Calendar tab now exists in the DOM

## Why Data Isn't Showing

The Whale Tracker and Economic Calendar tabs are showing empty because **the database hasn't been initialized with data yet**. The migrations exist, but the data needs to be populated.

## Required Steps to Initialize Data

### 1. Run Database Migrations

The migrations need to be run on Railway:

```bash
# Connect to Railway database
railway connect postgres

# Then run the migrations:
\i src/database/migrations/004_whale_tracking.sql
\i src/database/migrations/005_economic_calendar.sql
```

Or use the initialization scripts:

```bash
# For Economic Calendar (automated)
python scripts/init_economic_calendar.py
```

### 2. Initialize Whale Tracker Data

The whale tracker needs to discover and index whales from Polymarket:

```bash
# Option 1: Use the API endpoint (if available)
curl -X POST https://web-production-c490dd.up.railway.app/api/whales/discover

# Option 2: Run the service directly
python -c "
from src.database.connection import AsyncSessionLocal
from src.services.whale_tracker import WhaleTracker
import asyncio

async def init():
    async with AsyncSessionLocal() as db:
        tracker = WhaleTracker(db)
        await tracker.discover_whales()
        await tracker.index_whales()
        await tracker.close()

asyncio.run(init())
"
```

### 3. Initialize Economic Calendar Data

The economic calendar needs to be populated with 2026 events:

```bash
# Use the automated script
python scripts/init_economic_calendar.py
```

This script:
- Runs the database migration automatically
- Initializes 2026 FOMC, CPI, NFP, GDP events
- Matches markets to events using keyword analysis

### 4. Verify Data

After initialization, check the browser console:
- Open Developer Tools (F12)
- Go to Console tab
- Click on "🐋 Whale Tracker" or "📅 Economic Calendar"
- You should see console.log messages showing the API response

If you see empty arrays `[]`, the data hasn't been initialized yet.

## Expected Console Output

**When data is loaded:**
```
Whale leaderboard data: [{rank: 1, wallet_address: "0x...", ...}, ...]
Calendar events data: [{id: 1, event_type: "FOMC", ...}, ...]
```

**When data is empty:**
```
Whale leaderboard data: []
Calendar events data: []
```

## Next Steps

1. **Run migrations on Railway** (if not already done)
2. **Initialize whale tracker** (discover whales from Polymarket subgraph)
3. **Initialize economic calendar** (run `scripts/init_economic_calendar.py`)
4. **Refresh the browser** and check the tabs again

## API Endpoints

The following endpoints should return data after initialization:

- `GET /api/whales/leaderboard?limit=50` - Returns whale leaderboard
- `GET /api/whales/recent-activity?hours=24` - Returns recent whale trades
- `GET /api/whales/alerts?unread_only=true` - Returns whale alerts
- `GET /api/calendar/upcoming?days=30` - Returns upcoming economic events
- `GET /api/calendar/event/{event_id}/markets` - Returns markets related to an event

## Troubleshooting

If data still doesn't show after initialization:

1. **Check Railway logs** for errors:
   ```bash
   railway logs
   ```

2. **Test API endpoints directly**:
   ```bash
   curl https://web-production-c490dd.up.railway.app/api/whales/leaderboard?limit=10
   curl https://web-production-c490dd.up.railway.app/api/calendar/upcoming?days=30
   ```

3. **Check browser console** for JavaScript errors or API errors

4. **Verify database tables exist**:
   ```sql
   SELECT COUNT(*) FROM whale_wallets;
   SELECT COUNT(*) FROM economic_events;
   ```

