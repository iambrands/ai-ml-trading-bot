# Background Service on Railway

## Overview

On your **local environment**, you had a background service (`background_prediction_service.py`) running that automatically generated predictions every 5 minutes.

For **Railway**, we need a different approach since Railway runs containers, not background scripts.

---

## Options for Railway

### Option 1: Railway Cron Jobs (Recommended)

Railway supports scheduled jobs via cron-like syntax.

**How it works**:
- Railway runs scheduled tasks at specified intervals
- Can call your API endpoint periodically
- No need for background scripts

**Setup**:
1. **Go to Railway Dashboard**
2. **Navigate to your project**
3. **Add a new service** or use existing service
4. **Configure cron job** to call prediction endpoint every 5 minutes

**Example cron job**:
```bash
# Run every 5 minutes
*/5 * * * * curl -X POST https://web-production-c490dd.up.railway.app/predictions/generate?limit=20
```

**Note**: Railway's cron job feature may vary - check Railway documentation for current cron support.

---

### Option 2: Background Service Script (Alternative)

Run the background service script as a separate service on Railway.

**How it works**:
- Deploy background service script as separate Railway service
- Runs continuously, calling API endpoint every 5 minutes
- Similar to local setup

**Setup**:
1. **Modify background service** to use Railway URL
2. **Deploy as separate service** on Railway
3. **Configure to call Railway API endpoint**

**Update script**:
```python
# In scripts/background_prediction_service.py
API_BASE = os.getenv("API_BASE_URL", "https://web-production-c490dd.up.railway.app")
```

**Deploy**:
- Create new Railway service
- Point to background service script
- Set `API_BASE_URL` environment variable
- Deploy

---

### Option 3: Modify Main API Service (Simple)

Add prediction generation to the main API service startup.

**How it works**:
- Start background thread/task when API service starts
- Runs prediction generation every 5 minutes
- All in one service

**Implementation**:
- Add background task to FastAPI startup
- Use `asyncio` to run periodic prediction generation
- Integrate with existing API service

**Pros**: Simple, one service  
**Cons**: Couples prediction generation with API service

---

### Option 4: External Cron Service (External)

Use external cron service (e.g., cron-job.org, EasyCron) to call Railway API.

**How it works**:
- External service calls Railway API endpoint periodically
- No Railway-specific setup needed
- Works from outside Railway

**Setup**:
1. Sign up for cron service (cron-job.org, EasyCron, etc.)
2. Configure job to call Railway API every 5 minutes
3. Set URL: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`

**Pros**: Simple, no Railway-specific setup  
**Cons**: External dependency

---

## Recommended: Option 1 or Option 4

### For Railway Native: Option 1 (Railway Cron)

If Railway supports cron jobs:
- Native Railway feature
- No external dependencies
- Integrated with Railway platform

### For Simplicity: Option 4 (External Cron)

If Railway doesn't support cron jobs:
- Simple to set up
- Works reliably
- No Railway-specific setup

---

## Quick Setup: External Cron Service

### Step 1: Choose Cron Service

**Options**:
- **cron-job.org** (free tier available)
- **EasyCron** (free tier available)
- **UptimeRobot** (free tier available)

### Step 2: Configure Cron Job

1. **Sign up** for cron service
2. **Create new cron job**
3. **Set URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
4. **Set method**: POST
5. **Set schedule**: Every 5 minutes (`*/5 * * * *`)
6. **Save**

### Step 3: Test

1. **Wait 5 minutes**
2. **Check Railway dashboard** for new predictions
3. **Verify** predictions are being generated

---

## Current Status

**Local Environment**:
- ✅ Background service running (`background_prediction_service.py`)
- ✅ Generates predictions every 5 minutes
- ✅ Calls local API: `http://localhost:8002`

**Railway Environment**:
- ✅ API endpoint working
- ✅ Can generate predictions manually
- ⏳ Need to set up automated generation

---

## Summary

**For Railway, you have options**:

1. **Railway Cron** (if supported) - Native Railway feature
2. **External Cron Service** (recommended for simplicity) - cron-job.org, EasyCron, etc.
3. **Background Service Script** - Deploy as separate service
4. **Integrated Background Task** - Add to main API service

**Recommended**: External Cron Service (Option 4) for simplicity and reliability.

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*



