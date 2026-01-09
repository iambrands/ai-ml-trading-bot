# Railway Deployment Guide

## Overview

This guide will help you deploy the Polymarket AI Trading Bot to Railway for cloud testing and production use.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub (already done)
3. **Environment Variables**: Prepare your API keys and configuration

## Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `iambrands/ai-ml-trading-bot`
5. Select the `main` branch

## Step 2: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

### Required Variables

```env
# Database (Railway will provide PostgreSQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<railway-generated>
POSTGRES_DB=railway
POSTGRES_HOST=<railway-provided>
POSTGRES_PORT=5432

# API Keys
POLYMARKET_API_KEY=your_polymarket_key
POLYMARKET_PRIVATE_KEY=your_private_key
NEWSAPI_KEY=your_newsapi_key

# Optional (if you have them)
TWITTER_API_KEY=your_twitter_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# Trading Configuration
INITIAL_CAPITAL=100.0
MAX_POSITION_SIZE=5.0
MIN_EDGE_THRESHOLD=0.10
MIN_CONFIDENCE=0.60
```

### Railway PostgreSQL Setup

1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically create:
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`
3. These are automatically injected as environment variables

## Step 3: Configure Build Settings

Railway will automatically detect:
- **Python** (from `requirements.txt` and `runtime.txt`)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: From `Procfile` (uses PYTHONPATH for proper imports)

### Verify Configuration

1. Go to Settings → Service
2. Check "Start Command" is: `PYTHONPATH=$PWD:$PYTHONPATH python -m uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`
3. Check "Healthcheck Path" (optional): `/health`

### Important: Python Path

The `Procfile` includes `PYTHONPATH=$PWD:$PYTHONPATH` to ensure Python can find the `src` module. This is required because Railway runs from the project root, and we need to import `src.api.app`.

## Step 4: Deploy

1. Railway will automatically deploy when you push to GitHub
2. Or click "Deploy" in Railway dashboard
3. Watch the build logs for progress

## Step 5: Initialize Database

After first deployment, initialize the database:

### Option 1: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run database initialization
railway run python scripts/init_db.py
```

### Option 2: Railway Web Console

1. Go to your service in Railway
2. Click "Deployments" → "Latest" → "View Logs"
3. Use the web terminal to run:
   ```bash
   python scripts/init_db.py
   ```

## Step 6: Update UI API Base URL

The UI needs to know the Railway URL. Update the API base:

### Option 1: Environment Variable (Recommended)

Add to Railway variables:
```env
API_BASE_URL=https://your-app-name.railway.app
```

Then update `src/api/app.py` to inject this into the HTML template.

### Option 2: Manual Update

After deployment, get your Railway URL and update `src/api/static/index.html`:

```javascript
// Change from:
const API_BASE = 'http://localhost:8001';

// To:
const API_BASE = 'https://your-app-name.railway.app';
```

## Step 7: Access Your Application

1. Railway will provide a URL like: `https://your-app-name.railway.app`
2. Access the dashboard at: `https://your-app-name.railway.app/dashboard`
3. Access API docs at: `https://your-app-name.railway.app/docs`

## Step 8: Set Up Background Service (Optional)

For continuous prediction generation, you can:

### Option 1: Railway Cron Job (Recommended)

1. Add a new service in Railway
2. Use "Cron Job" template
3. Schedule: `*/5 * * * *` (every 5 minutes)
4. Command: `curl -X POST https://your-app-name.railway.app/predictions/generate`

### Option 2: Background Worker Service

1. Add a new service in Railway
2. Set start command: `python scripts/background_prediction_service.py`
3. Update `API_BASE` in the script to your Railway URL

## Configuration Files

### Procfile
```
web: uvicorn src.api.app:app --host 0.0.0.0 --port $PORT
```

### railway.json
Already created with proper configuration.

## Environment-Specific Settings

### Production Considerations

1. **Database**: Use Railway PostgreSQL (automatically provided)
2. **Static Files**: Serve from Railway (already configured)
3. **Logging**: Railway captures all logs automatically
4. **Scaling**: Railway auto-scales based on traffic

### Security

1. **API Keys**: Store in Railway environment variables (never commit)
2. **Database**: Railway PostgreSQL is secure by default
3. **HTTPS**: Railway provides SSL automatically
4. **CORS**: Update CORS settings if needed for your domain

## Monitoring

### Railway Dashboard

- **Metrics**: CPU, Memory, Network
- **Logs**: Real-time application logs
- **Deployments**: Deployment history
- **Health**: Service health status

### Application Health

- Health endpoint: `https://your-app-name.railway.app/health`
- API docs: `https://your-app-name.railway.app/docs`

## Troubleshooting

### Build Fails

1. Check build logs in Railway dashboard
2. Verify `requirements.txt` has all dependencies
3. Check Python version (Railway auto-detects from `runtime.txt` or `requirements.txt`)

### Database Connection Issues

1. Verify PostgreSQL service is running
2. Check environment variables are set correctly
3. Verify database was initialized: `railway run python scripts/init_db.py`

### API Not Responding

1. Check service logs in Railway
2. Verify port is set to `$PORT` (Railway provides this)
3. Check health endpoint: `/health`

### UI Can't Connect to API

1. Update `API_BASE` in `index.html` to Railway URL
2. Check CORS settings if accessing from different domain
3. Verify API is accessible: `curl https://your-app-name.railway.app/health`

## Cost Considerations

Railway pricing:
- **Free Tier**: $5 credit/month
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

**Estimated Costs**:
- PostgreSQL: ~$5/month
- Web Service: ~$5-10/month (depending on usage)
- Background Worker (if used): ~$5/month

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Initialize database
3. ✅ Update UI API URL
4. ✅ Test all endpoints
5. ✅ Set up background service (optional)
6. ✅ Monitor logs and metrics

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: GitHub repository

---

**Note**: Remember to update the UI's `API_BASE` URL after deployment to point to your Railway URL instead of `localhost:8001`.

