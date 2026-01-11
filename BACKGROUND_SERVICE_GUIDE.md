# Background Prediction Service Guide

## Overview

The background prediction service automatically generates predictions every 5 minutes, so you don't need to manually trigger prediction generation.

## How It Works

### Service Behavior

1. **Runs Continuously**: The service runs in the background 24/7
2. **Generates Predictions**: Every 5 minutes, it calls the API to generate predictions for active markets
3. **Auto-Creates Signals**: Signals are automatically created from predictions (if edge > threshold)
4. **Logs Everything**: All activity is logged to `logs/background_service.log`

### UI Auto-Refresh

**Important**: The UI auto-refresh (every 30 seconds) is **correct**, but it works like this:

- **Every 30 seconds**: The UI automatically checks the database for new data
- **If new data exists**: It appears automatically (no manual refresh needed)
- **If no new data**: The same data is shown (because nothing new was generated)

**Timeline**:
- 0:00 - Service generates predictions → Saved to database
- 0:30 - UI auto-refreshes → Shows new predictions ✅
- 1:00 - UI auto-refreshes → Same predictions (no new ones yet)
- 5:00 - Service generates new predictions → Saved to database
- 5:30 - UI auto-refreshes → Shows new predictions ✅

## Starting the Service

### Method 1: Background Process (Current)

```bash
# Start service
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
echo $! > logs/background_service.pid

# Check if running
ps -p $(cat logs/background_service.pid)

# View logs
tail -f logs/background_service.log
```

### Method 2: Terminal (for testing)

```bash
# Run in foreground (Ctrl+C to stop)
python scripts/background_prediction_service.py
```

### Method 3: Screen/Tmux (for remote servers)

```bash
# Using screen
screen -S prediction_service
python scripts/background_prediction_service.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r prediction_service
```

## Stopping the Service

```bash
# If using PID file
kill $(cat logs/background_service.pid)
rm logs/background_service.pid

# Or find and kill manually
ps aux | grep background_prediction_service
kill <PID>
```

## Monitoring

### Check Service Status

```bash
# Check if process is running
ps aux | grep background_prediction_service

# Check logs
tail -f logs/background_service.log

# Check recent activity
tail -50 logs/background_service.log | grep "Generating predictions"
```

### Expected Log Output

```
2026-01-09 14:00:00 [INFO] Starting background prediction service
2026-01-09 14:00:00 [INFO] API Base: http://localhost:8001
2026-01-09 14:00:00 [INFO] Update Interval: 300 seconds (5.0 minutes)
2026-01-09 14:00:00 [INFO] Generating predictions at 2026-01-09 14:00:00 CST
2026-01-09 14:00:05 [INFO] Predictions generated successfully
2026-01-09 14:00:05 [INFO] Next update in 300 seconds (5.0 minutes)
```

## Configuration

### Change Update Interval

Edit `scripts/background_prediction_service.py`:

```python
INTERVAL = 300  # Change to desired seconds (e.g., 600 for 10 minutes)
```

### Change API Endpoint

Edit `scripts/background_prediction_service.py`:

```python
API_BASE = "http://localhost:8001"  # Change if API is on different host/port
```

## Troubleshooting

### Service Not Running

1. **Check if API is running**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Check logs for errors**:
   ```bash
   tail -100 logs/background_service.log
   ```

3. **Restart service**:
   ```bash
   # Stop old process
   kill $(cat logs/background_service.pid) 2>/dev/null
   
   # Start new process
   nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
   echo $! > logs/background_service.pid
   ```

### No New Predictions Appearing

1. **Check service is running**:
   ```bash
   ps aux | grep background_prediction_service
   ```

2. **Check service logs**:
   ```bash
   tail -50 logs/background_service.log
   ```

3. **Check API logs** (if API server is running):
   ```bash
   # Check API server output for errors
   ```

4. **Verify database has new predictions**:
   ```sql
   SELECT prediction_time, market_id, edge 
   FROM predictions 
   ORDER BY prediction_time DESC 
   LIMIT 10;
   ```

### Service Crashes

The service will automatically retry on failures, but if it crashes completely:

1. **Check error logs**:
   ```bash
   tail -100 logs/background_service.log | grep ERROR
   ```

2. **Restart service**:
   ```bash
   nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
   echo $! > logs/background_service.pid
   ```

3. **Consider using systemd/launchd** for automatic restart (see DATA_UPDATE_GUIDE.md)

## Timezone

All timestamps in the service and UI are displayed in **Central Time (CT)**:
- CST (Central Standard Time) in winter
- CDT (Central Daylight Time) in summer

The service automatically handles timezone conversion.

## Summary

✅ **Service runs automatically** - No manual intervention needed
✅ **Generates predictions every 5 minutes** - Continuous updates
✅ **UI auto-refreshes every 30 seconds** - Shows new data when available
✅ **No manual refresh needed** - Just wait and new data appears
✅ **All times in Central Time** - Matches your timezone

**You don't need to click "Refresh"** - the UI automatically shows new data when it's generated!


