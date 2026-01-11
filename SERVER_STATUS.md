# Server Status & Troubleshooting

## Current Issue: Server Not Responding

### Problem Summary
- Server process is running (PID: 74606) on port 8001
- But server is not responding to HTTP requests
- Error: "Address already in use" when trying to restart
- Network errors: `ERR_NETWORK_CHANGED` in browser

### Likely Causes

1. **Port Conflict**: Multiple processes trying to use port 8001
2. **Server Hang**: Server started but hung during initialization
3. **Database Connection**: Server waiting for database that's not responding
4. **Import Errors**: Server crashed during startup but process still exists

### Diagnostic Steps

#### 1. Check Running Processes
```bash
# Check all processes on port 8001
lsof -i :8001

# Check uvicorn processes
ps aux | grep uvicorn | grep -v grep
```

#### 2. Kill Existing Processes
```bash
# Kill all uvicorn processes
pkill -f "uvicorn.*8001"

# Or kill specific PID
kill 74606

# Force kill if needed
kill -9 74606
```

#### 3. Test Server Response
```bash
# Test health endpoint
curl -v http://localhost:8001/health

# Check server logs
tail -f logs/api_server.log
```

#### 4. Check for Import Errors
```bash
# Test if app can import
python -c "from src.api.app import app; print('OK')"
```

## Solution: Move to Port 8002

### Option 1: Update Configuration to Use Port 8002

**Update `scripts/start_api.sh`**:
```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8002 --reload
```

**Update `src/api/static/index.html`** (only for localhost):
- The UI now auto-detects `window.location.origin`, so it will work on any port automatically

**Update `.env` or environment** (if using):
```
API_PORT=8002
```

### Option 2: Fix Port 8001 Issue

**Complete Clean Restart**:
```bash
# Kill all processes
pkill -f uvicorn

# Wait a moment
sleep 2

# Check port is free
lsof -i :8001

# Start fresh
cd /Users/iabadvisors/ai-ml-trading-bot
uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
```

## Recommended Action: Switch to Port 8002

Since port 8001 appears to have conflicts, let's switch to port 8002 for a clean start.


