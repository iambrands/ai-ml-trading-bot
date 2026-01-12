# Polymarket API Setup Guide

## Current Issue

The Polymarket API is returning `403 Forbidden` errors when trying to fetch market data. This typically means:

1. **API Authentication Required**: The API may require an API key or authentication token
2. **Endpoint Changes**: The API endpoints may have changed
3. **Rate Limiting**: The API may be blocking requests due to rate limits

## Solutions

### Option 1: Check Polymarket API Documentation

1. Visit the official Polymarket API documentation:
   - https://docs.polymarket.com
   - https://github.com/Polymarket/agents

2. Check for:
   - Required authentication methods
   - Current API endpoints
   - Rate limiting policies
   - API key registration process

### Option 2: Add API Key to Environment

If Polymarket requires an API key, add it to your `.env` file:

```bash
POLYMARKET_API_KEY=your_api_key_here
```

The code will automatically use this key for authentication.

### Option 3: Use Alternative Data Sources

For training purposes, you can:

1. **Manual Data Collection**: Export market data manually from Polymarket's website
2. **Use Public APIs**: Check if Polymarket has a public GraphQL endpoint or other public APIs
3. **Historical Data**: Use previously collected data if available

### Option 4: Mock Data for Testing

For development and testing, you can create a mock data provider that generates synthetic training data. This allows you to test the training pipeline without API access.

## Current Implementation

The code now:
- ✅ Tries multiple endpoint variations automatically
- ✅ Handles 403 errors gracefully
- ✅ Provides helpful error messages
- ✅ Supports API key authentication if configured
- ✅ Returns empty list instead of crashing

## Next Steps

1. **Check Polymarket Documentation**: Verify the correct API endpoints and authentication method
2. **Get API Credentials**: If required, register for API access and get credentials
3. **Update Configuration**: Add credentials to `.env` file
4. **Test Connection**: Run the training script again to verify API access

## Alternative: Use py-clob-client

The project includes `py-clob-client` which is Polymarket's official Python client. You may need to use this instead of direct API calls:

```python
from py_clob_client.client import ClobClient

client = ClobClient(...)
# Use client methods instead of direct HTTP calls
```

Check the py-clob-client documentation for proper usage.



