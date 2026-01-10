# Railway Environment Variables Guide

This guide lists all environment variables you should add to Railway for the Polymarket AI Trading Bot.

## Required Variables (Minimum to Run)

### 1. PORT (Critical)
- **Name**: `PORT`
- **Value**: `8000` (or let Railway set it automatically)
- **Purpose**: Server port for the FastAPI application
- **Status**: Railway should set this automatically, but if not, add it manually
- **Required**: ✅ Yes (for deployment)

---

## API Keys (For Core Functionality)

### 2. NewsAPI Key
- **Name**: `NEWSAPI_KEY`
- **Value**: Your NewsAPI key (e.g., `46ba59f50bcf4d2398fecba3f8776c84`)
- **Purpose**: Fetch news articles for sentiment analysis
- **Get it**: https://newsapi.org/register (Free tier available)
- **Required**: ✅ Recommended (app works without it but with limited data)
- **Free Tier**: 100 requests/day

### 3. Polymarket API (Optional for now)
- **Name**: `POLYMARKET_API_KEY`
- **Value**: Your Polymarket API key (if available)
- **Purpose**: Authenticate with Polymarket API
- **Get it**: Check https://docs.polymarket.com
- **Required**: ❌ Optional (using py-clob-client which may not need it)
- **Note**: The app currently uses `py-clob-client` which may handle auth differently

### 4. Polymarket Private Key (Only for Trading)
- **Name**: `POLYMARKET_PRIVATE_KEY`
- **Value**: Your private key for executing trades
- **Purpose**: Execute real trades on Polymarket (only if you plan to trade live)
- **Get it**: From Polymarket when setting up trading account
- **Required**: ❌ Optional (only needed for live trading, not for predictions)

---

## Database (If Using PostgreSQL on Railway)

If you plan to use Railway's PostgreSQL service, Railway will automatically provide these variables. You can also add them manually:

### 5. PostgreSQL Connection (Auto-provided by Railway PostgreSQL service)
- **Name**: `POSTGRES_HOST`
- **Value**: Auto-set by Railway (usually `${{Postgres.PGHOST}}`)
- **Required**: ✅ Only if using PostgreSQL

- **Name**: `POSTGRES_PORT`
- **Value**: Auto-set by Railway (usually `5432`)
- **Required**: ✅ Only if using PostgreSQL

- **Name**: `POSTGRES_DB`
- **Value**: Auto-set by Railway (usually `${{Postgres.PGDATABASE}}`)
- **Required**: ✅ Only if using PostgreSQL

- **Name**: `POSTGRES_USER`
- **Value**: Auto-set by Railway (usually `${{Postgres.PGUSER}}`)
- **Required**: ✅ Only if using PostgreSQL

- **Name**: `POSTGRES_PASSWORD`
- **Value**: Auto-set by Railway (usually `${{Postgres.PGPASSWORD}}`)
- **Required**: ✅ Only if using PostgreSQL

**Note**: If you add a PostgreSQL service in Railway, Railway automatically creates these variables. You just need to reference them in your web service.

---

## Optional API Keys (For Enhanced Features)

### 6. Twitter/X API (Optional)
- **Name**: `TWITTER_API_KEY`
- **Value**: Your Twitter API key
- **Purpose**: Fetch tweets for social sentiment analysis
- **Get it**: https://developer.twitter.com/en/portal/dashboard
- **Required**: ❌ Optional (may require paid plan)
- **Cost**: Free tier limited, Basic tier $100/month

- **Name**: `TWITTER_API_SECRET`
- **Name**: `TWITTER_ACCESS_TOKEN`
- **Name**: `TWITTER_ACCESS_TOKEN_SECRET`
- **Required**: ❌ Only if using Twitter API

### 7. Reddit API (Optional)
- **Name**: `REDDIT_CLIENT_ID`
- **Value**: Your Reddit app client ID
- **Purpose**: Fetch Reddit posts for social sentiment analysis
- **Get it**: https://www.reddit.com/prefs/apps
- **Required**: ❌ Optional (free to use)
- **Note**: You already have a Reddit API request pending

- **Name**: `REDDIT_CLIENT_SECRET`
- **Value**: Your Reddit app secret
- **Required**: ❌ Only if using Reddit API

- **Name**: `REDDIT_USER_AGENT`
- **Value**: `polymarket-ai-trader/0.1.0` (or your app name)
- **Required**: ❌ Only if using Reddit API

---

## Configuration Variables (Optional - Have Defaults)

### 8. Logging Level
- **Name**: `LOG_LEVEL`
- **Value**: `INFO` (or `DEBUG`, `WARNING`, `ERROR`)
- **Default**: `INFO`
- **Required**: ❌ Optional

### 9. Polymarket API URL
- **Name**: `POLYMARKET_API_URL`
- **Value**: `https://api.polymarket.com`
- **Default**: Already set
- **Required**: ❌ Optional

---

## Quick Setup Checklist

### Minimum Required (Just to Deploy):
1. ✅ **PORT** = `8000` (or let Railway set automatically)

### Recommended for Basic Functionality:
1. ✅ **PORT** = `8000`
2. ✅ **NEWSAPI_KEY** = Your NewsAPI key (you already have this: `46ba59f50bcf4d2398fecba3f8776c84`)

### Optional but Useful:
3. ❓ **POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD** (if using Railway PostgreSQL)
4. ❓ **REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET** (when Reddit API is approved)
5. ❓ **POLYMARKET_API_KEY** (if available/needed)

---

## How to Add Variables in Railway

1. Go to your Railway project dashboard
2. Click on your service (`web`)
3. Go to the **"Variables"** tab
4. Click **"+ New Variable"**
5. Enter the **Name** and **Value**
6. Click **"Add"**
7. Railway will automatically redeploy with the new variables

---

## Variables You Already Have Locally

Based on your setup, you already have:
- ✅ `NEWSAPI_KEY` = `46ba59f50bcf4d2398fecba3f8776c84`

You should add this to Railway!

---

## Priority Order for Railway Setup

**Phase 1 (Minimum - Get it Running):**
1. `PORT` = `8000`

**Phase 2 (Basic Functionality):**
2. `NEWSAPI_KEY` = `46ba59f50bcf4d2398fecba3f8776c84`

**Phase 3 (If Using Database on Railway):**
3. Add PostgreSQL service in Railway (Railway auto-creates DB variables)
4. Link the PostgreSQL service to your web service
5. Railway will automatically provide `POSTGRES_HOST`, `POSTGRES_PORT`, etc.

**Phase 4 (When Ready):**
6. `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` (when Reddit API is approved)
7. `POLYMARKET_API_KEY` (if available/needed)

---

## Notes

- **Secrets**: Railway treats all environment variables as secrets - they won't be visible in logs
- **Reference Variables**: If you add a PostgreSQL service, Railway creates variables like `${{Postgres.PGHOST}}` that you can reference
- **Auto-redeploy**: Railway automatically redeploys when you add/modify variables
- **Case Sensitivity**: Environment variable names are typically uppercase (e.g., `NEWSAPI_KEY`)

---

## Current Status

✅ You have: `NEWSAPI_KEY`  
❓ Pending: Reddit API approval  
❓ Optional: Twitter API (may require payment)  
❓ Optional: Polymarket API key (check if needed with py-clob-client)

