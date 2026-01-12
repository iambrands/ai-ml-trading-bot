# API Keys Setup Guide

This guide provides direct links to obtain API keys for all services used by the Polymarket AI Trading Bot.

## Required API Keys

### 1. Polymarket API

**Status**: The Polymarket API appears to require authentication, but the exact registration process may vary.

**Links**:
- **Official Documentation**: https://docs.polymarket.com
- **GitHub Agents Repository**: https://github.com/Polymarket/agents
- **Polymarket Website**: https://polymarket.com
- **CLOB Client (Python)**: https://github.com/Polymarket/py-clob-client

**Notes**:
- Check the official documentation for API key registration
- You may need to contact Polymarket support for API access
- The `py-clob-client` library may handle authentication differently
- Some endpoints may be public, others may require authentication

**Environment Variable**:
```bash
POLYMARKET_API_KEY=your_key_here
POLYMARKET_PRIVATE_KEY=your_private_key_here  # For trading
```

---

### 2. NewsAPI

**Purpose**: Fetch news articles for sentiment analysis

**Registration Links**:
- **Sign Up (Free Tier)**: https://newsapi.org/register
- **API Documentation**: https://newsapi.org/docs
- **Dashboard**: https://newsapi.org/account

**Free Tier Limits**:
- 100 requests/day
- 1,000 results/request
- Development use only

**Paid Plans**: Available for production use

**Environment Variable**:
```bash
NEWSAPI_KEY=your_api_key_here
```

**How to Get**:
1. Go to https://newsapi.org/register
2. Sign up with email
3. Verify your email
4. Copy API key from dashboard
5. Add to `.env` file

---

### 3. Twitter/X API

**Purpose**: Fetch tweets for social sentiment analysis

**Registration Links**:
- **Developer Portal**: https://developer.twitter.com/en/portal/dashboard
- **Apply for Access**: https://developer.twitter.com/en/portal/petition/essential/basic-info
- **API Documentation**: https://developer.twitter.com/en/docs/twitter-api
- **Pricing**: https://developer.twitter.com/en/pricing

**API Tiers**:
- **Free Tier**: Limited (may require approval)
- **Basic Tier**: $100/month
- **Pro Tier**: $5,000/month

**Required Credentials**:
- API Key
- API Secret
- Access Token
- Access Token Secret

**Environment Variables**:
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

**How to Get**:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new project/app
3. Generate API keys and tokens
4. Copy credentials to `.env` file

**Note**: Twitter API access has become more restricted. You may need to apply for access.

---

### 4. Reddit API

**Purpose**: Fetch Reddit posts for social sentiment analysis

**Registration Links**:
- **Reddit Apps**: https://www.reddit.com/prefs/apps
- **API Documentation**: https://www.reddit.com/dev/api/
- **PRAW Documentation**: https://praw.readthedocs.io/

**Free to Use**: Reddit API is free but requires registration

**Required Credentials**:
- Client ID
- Client Secret
- User Agent (your app name)

**Environment Variables**:
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=polymarket-ai-trader/0.1.0
```

**How to Get**:
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app" or "create app"
3. Fill in:
   - **Name**: Your app name (e.g., "Polymarket AI Trader")
   - **Type**: Select "script"
   - **Description**: Brief description
   - **Redirect URI**: `http://localhost:8080` (or any valid URI)
4. Click "create app"
5. Copy the **client ID** (under the app name) and **secret** (labeled "secret")
6. Add to `.env` file

**Note**: The client ID is the string under your app name, and the secret is labeled "secret" in the app details.

---

## Quick Setup Checklist

1. **NewsAPI** ✅ (Easiest - Free tier available)
   - Sign up: https://newsapi.org/register
   - Get key from dashboard
   - Add `NEWSAPI_KEY` to `.env`

2. **Reddit API** ✅ (Free - Easy setup)
   - Create app: https://www.reddit.com/prefs/apps
   - Get Client ID and Secret
   - Add `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` to `.env`

3. **Twitter/X API** ⚠️ (May require paid plan)
   - Apply: https://developer.twitter.com/en/portal/dashboard
   - May need to pay for access
   - Add credentials to `.env`

4. **Polymarket API** ❓ (Check documentation)
   - Check: https://docs.polymarket.com
   - May need to contact support
   - Add `POLYMARKET_API_KEY` to `.env` if available

---

## Environment File Template

Create a `.env` file in the project root with:

```bash
# Polymarket API
POLYMARKET_API_URL=https://api.polymarket.com
POLYMARKET_API_KEY=your_polymarket_key_here
POLYMARKET_PRIVATE_KEY=your_private_key_for_trading

# NewsAPI
NEWSAPI_KEY=your_newsapi_key_here

# Twitter/X API
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=polymarket-ai-trader/0.1.0

# Database (if using)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=polymarket_trader
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis (if using)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## Priority Order

**For Basic Functionality** (can work without all APIs):
1. **NewsAPI** - Easiest to get, free tier available
2. **Reddit API** - Free, easy setup
3. **Twitter API** - Optional, may require payment
4. **Polymarket API** - Required for market data, check documentation

**Minimum Required**:
- At least one data source (NewsAPI or Reddit) for sentiment analysis
- Polymarket API access for market data (may need alternative approach)

---

## Troubleshooting

### Polymarket API 403 Error
- Check if API key is required
- Verify endpoint URLs in documentation
- Consider using `py-clob-client` library instead
- Contact Polymarket support if needed

### Twitter API Access Denied
- Twitter has restricted free API access
- May need to pay for Basic tier ($100/month)
- Consider making Twitter optional for initial testing

### Rate Limits
- NewsAPI: 100 requests/day (free tier)
- Reddit: 60 requests/minute (default)
- Twitter: Varies by tier
- Implement caching to reduce API calls

---

## Alternative Approaches

If you can't get all API keys:

1. **Start with NewsAPI + Reddit**: These are easiest to get
2. **Skip Twitter initially**: Can add later
3. **Use mock data for Polymarket**: For testing the training pipeline
4. **Manual data collection**: Export market data manually for training

The bot will work with partial API access - it will just have limited data sources.



