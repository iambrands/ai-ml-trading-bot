# Data Update Guide

## Understanding Data Updates

### Current State

**✅ Background Service Available**: A background Python service is available that automatically generates predictions every 5 minutes. This is the recommended approach for continuous operation.

### Why Data Appears Static

If you're seeing the same data for hours, it's because:

1. **Background Service Not Running**: The background service must be started to generate predictions automatically
2. **No Manual Triggers**: If the service isn't running, predictions must be generated via API call or script
3. **UI Auto-Refresh**: The UI refreshes every 30 seconds, but it's showing the same data from the database (because no new predictions were generated)

---

## How to Generate New Data

### Option 1: Background Service (Recommended for Production)

**Best Option**: Run the background service for automatic, continuous prediction generation.

**Start the Service**:
```bash
# Start in background
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
echo $! > logs/background_service.pid

# Check if running
ps -p $(cat logs/background_service.pid)

# View logs
tail -f logs/background_service.log
```

**What It Does**:
- ✅ Runs automatically 24/7
- ✅ Generates predictions every 5 minutes
- ✅ Automatically creates signals
- ✅ Logs all activity
- ✅ Handles errors and retries
- ✅ "Set it and forget it" solution

**Stop the Service**:
```bash
kill $(cat logs/background_service.pid)
rm logs/background_service.pid
```

**See**: `BACKGROUND_SERVICE_GUIDE.md` for complete documentation.

### Option 2: API Endpoint (For Testing/Debugging)

**Trigger prediction generation via API**:

```bash
# Generate predictions for active markets
curl -X POST http://localhost:8001/predictions/generate

# With auto-trades enabled (generates signals and trades automatically)
curl -X POST http://localhost:8001/predictions/generate?auto_trades=true
```

**What This Does**:
1. Fetches active markets from Polymarket
2. Generates features for each market
3. Runs ML models to create predictions
4. Automatically generates signals (if edge > threshold)
5. Automatically executes trades (if auto_trades=true)
6. Updates portfolio

**Frequency**: Use this for testing or one-off runs. For continuous operation, use the background service instead.

### Option 3: Python Script

```bash
# Generate predictions only
python scripts/generate_predictions.py

# Generate predictions + signals + trades
python scripts/generate_predictions.py --auto-trades
```

### Option 4: Scheduled Automation (Cron) - Alternative to Background Service

**Set up a cron job to run every 5 minutes**:

```bash
# Edit crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * curl -X POST http://localhost:8001/predictions/generate >> /tmp/prediction_log.txt 2>&1
```

**Or use a Python script**:

```bash
# Create a script
cat > scripts/auto_generate_predictions.sh << 'EOF'
#!/bin/bash
cd /Users/iabadvisors/ai-ml-trading-bot
python scripts/generate_predictions.py --auto-trades
EOF

chmod +x scripts/auto_generate_predictions.sh

# Add to crontab
*/5 * * * * /Users/iabadvisors/ai-ml-trading-bot/scripts/auto_generate_predictions.sh
```

---

## Verifying Data Updates

### 1. Check Database Timestamps

**Connect to PostgreSQL**:
```bash
psql -U iabadvisors -d polymarket_trader
```

**Check latest predictions**:
```sql
SELECT 
    prediction_time,
    market_id,
    edge,
    confidence,
    model_probability,
    market_price
FROM predictions 
ORDER BY prediction_time DESC 
LIMIT 10;
```

**Check latest signals**:
```sql
SELECT 
    created_at,
    market_id,
    signal_strength,
    executed,
    side
FROM signals 
ORDER BY created_at DESC 
LIMIT 10;
```

**Check latest trades**:
```sql
SELECT 
    entry_time,
    market_id,
    status,
    side,
    size,
    pnl
FROM trades 
ORDER BY entry_time DESC 
LIMIT 10;
```

### 2. Check API Endpoints

**Get latest predictions**:
```bash
curl http://localhost:8001/predictions?limit=5 | jq
```

**Get latest signals**:
```bash
curl http://localhost:8001/signals?limit=5 | jq
```

**Get latest trades**:
```bash
curl http://localhost:8001/trades?limit=5 | jq
```

### 3. UI Indicators

**On Each Tab**:
- "Last updated: [time]" shows when data was last refreshed
- Data refreshes automatically every 30 seconds
- New rows should appear if new data is generated

**Markets Tab**:
- Shows live data from Polymarket API
- Updates every 30 seconds automatically

**Predictions/Signals/Trades Tabs**:
- Shows data from database
- Only updates if new data is generated and saved

### 4. Check Logs

**Application Logs**:
```bash
tail -f logs/trading_bot.log
```

**Training Logs** (if training models):
```bash
tail -f logs/training_*.log
```

---

## Setting Up Continuous Updates

### Method 1: Simple Cron Job

**Create a script** (`scripts/continuous_updates.sh`):
```bash
#!/bin/bash
cd /Users/iabadvisors/ai-ml-trading-bot

# Generate predictions every 5 minutes
while true; do
    echo "$(date): Generating predictions..."
    curl -X POST http://localhost:8001/predictions/generate?auto_trades=true
    sleep 300  # Wait 5 minutes
done
```

**Run in background**:
```bash
chmod +x scripts/continuous_updates.sh
nohup ./scripts/continuous_updates.sh > logs/continuous_updates.log 2>&1 &
```

### Method 3: Systemd Service (Linux) or Launchd (macOS)

**macOS Launchd** (`com.polymarket.updates.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.polymarket.updates</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/curl</string>
        <string>-X</string>
        <string>POST</string>
        <string>http://localhost:8001/predictions/generate?auto_trades=true</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

**Install**:
```bash
cp com.polymarket.updates.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.polymarket.updates.plist
```

### Method 4: Python Background Service (Already Implemented)

**Note**: This is already implemented as `scripts/background_prediction_service.py`. See Method 1 above or `BACKGROUND_SERVICE_GUIDE.md` for usage.

**Create** (`scripts/background_service.py`):
```python
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/background_service.log'),
        logging.StreamHandler()
    ]
)

API_BASE = "http://localhost:8001"
INTERVAL = 300  # 5 minutes

while True:
    try:
        logging.info("Triggering prediction generation...")
        response = requests.post(f"{API_BASE}/predictions/generate?auto_trades=true", timeout=60)
        if response.status_code == 200:
            logging.info("Predictions generated successfully")
        else:
            logging.warning(f"API returned status {response.status_code}")
    except Exception as e:
        logging.error(f"Error generating predictions: {e}")
    
    logging.info(f"Sleeping for {INTERVAL} seconds...")
    time.sleep(INTERVAL)
```

**Run**:
```bash
python scripts/background_service.py &
```

---

## Troubleshooting

### No New Predictions Generated

**Possible Causes**:
1. **No Active Markets**: Check if Polymarket has active markets
   ```bash
   curl http://localhost:8001/live/markets?limit=5
   ```

2. **API Errors**: Check logs for API failures
   ```bash
   tail -f logs/trading_bot.log | grep ERROR
   ```

3. **Model Files Missing**: Ensure models are trained
   ```bash
   ls -lh data/models/*.pkl
   ```

4. **Database Connection Issues**: Check database is running
   ```bash
   psql -U iabadvisors -d polymarket_trader -c "SELECT 1;"
   ```

### Predictions Generated But No Signals

**Possible Causes**:
1. **Edge Too Low**: Predictions need edge > 5% (configurable)
   - Check predictions: `SELECT edge, confidence FROM predictions ORDER BY prediction_time DESC LIMIT 10;`
   - Lower threshold in Settings tab

2. **Confidence Too Low**: Predictions need confidence > 60% (configurable)
   - Check confidence scores
   - Lower threshold in Settings tab

### Signals Generated But No Trades

**Possible Causes**:
1. **Risk Limits**: Position limits or drawdown limits blocking trades
   - Check portfolio: `SELECT * FROM portfolio_snapshots ORDER BY snapshot_time DESC LIMIT 1;`
   - Adjust risk settings in Settings tab

2. **Auto-Trading Disabled**: Check if auto-trading is enabled
   - Settings tab → Trading Mode → Auto-Trade

3. **Insufficient Funds**: Not enough cash for position size
   - Check cash balance in Portfolio tab
   - Deposit more funds if needed

---

## Expected Update Frequency

### Recommendations

- **Predictions**: Every 5-15 minutes
  - Markets change frequently
  - News and sentiment update continuously
  - More frequent = more opportunities, but more API calls

- **Signals**: Generated automatically after predictions
  - No separate trigger needed
  - Generated if edge > threshold

- **Trades**: Generated automatically after signals (if auto-trading enabled)
  - No separate trigger needed
  - Executed if risk limits allow

- **Portfolio**: Updated automatically after trades
  - No separate trigger needed
  - Snapshot created after each trade

### Optimal Schedule

**For Active Trading**:
- Generate predictions every 5 minutes
- Monitor signals and trades in real-time
- Review portfolio hourly

**For Passive Trading**:
- Generate predictions every 15-30 minutes
- Let auto-trading handle execution
- Review portfolio daily

---

## Summary

**Key Points**:
1. ✅ **Background Service Available**: Use `scripts/background_prediction_service.py` for automatic updates (recommended)
2. ✅ **UI Auto-Refreshes**: Every 30 seconds (shows latest data when available)
3. ✅ **No Manual Refresh Needed**: Just wait - new data appears automatically
4. ✅ **Timezone**: All timestamps display in Central Time (CT)
5. ✅ **Verify Updates**: Check timestamps in database or service logs

**Next Steps**:
1. ✅ **Start Background Service** (if not already running):
   ```bash
   nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
   echo $! > logs/background_service.pid
   ```
2. ✅ **Monitor Service**: Check `logs/background_service.log` to see it working
3. ✅ **Check UI**: New data appears automatically every 30 seconds when generated
4. ✅ **Adjust Settings**: Change thresholds in Settings tab if needed

**Documentation**:
- `BACKGROUND_SERVICE_GUIDE.md` - Complete background service documentation
- `TECHNICAL_ARCHITECTURE.md` - Detailed technical information

**Current Status**:
- Background service generates predictions every 5 minutes
- UI auto-refreshes every 30 seconds
- All timestamps in Central Time (CT)
- No manual intervention needed!

