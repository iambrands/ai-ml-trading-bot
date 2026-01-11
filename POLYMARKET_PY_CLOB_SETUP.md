# Polymarket py-clob-client Setup Guide

Polymarket provides an official Python client library that we should use instead of direct API calls. This will handle authentication and API interactions properly.

## Official Polymarket Resources

### GitHub Repositories
- **py-clob-client**: https://github.com/Polymarket/py-clob-client
  - Official Python client for Polymarket CLOB (Central Limit Order Book)
  - 632 stars, actively maintained
  - MIT License

- **agents**: https://github.com/Polymarket/agents
  - AI agents for trading on Polymarket
  - 1.7k stars, great reference implementation
  - Shows how to build trading bots

- **clob-client** (TypeScript): https://github.com/Polymarket/clob-client
  - TypeScript version for reference

- **polymarket-subgraph**: https://github.com/Polymarket/polymarket-subgraph
  - For on-chain data indexing

### Documentation
- **Official Docs**: https://docs.polymarket.com
- **CLOB Client Docs**: Check the py-clob-client README

## Installation

The `py-clob-client` is already in your `requirements.txt`. To ensure it's installed:

```bash
pip install py-clob-client
```

Or if you need the latest version from GitHub:

```bash
pip install git+https://github.com/Polymarket/py-clob-client.git
```

## Using py-clob-client

### Basic Setup

```python
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.utilities import create_signed_order

# Initialize client
client = ClobClient(
    api_url="https://clob.polymarket.com",  # or testnet
    chain_id=POLYGON,
    private_key=your_private_key
)

# Get markets
markets = client.get_markets()
```

### Key Features

1. **Market Data**: Fetch active markets, resolved markets, market details
2. **Order Management**: Create, cancel, and manage orders
3. **Authentication**: Handles signing and authentication automatically
4. **WebSocket Support**: Real-time data updates

## Updating Our Implementation

We should update `src/data/sources/polymarket.py` to use `py-clob-client` instead of direct HTTP calls. This will:

1. ✅ Handle authentication properly
2. ✅ Use official API endpoints
3. ✅ Get better error messages
4. ✅ Support trading operations

## Migration Steps

1. **Update PolymarketDataSource** to use `ClobClient`
2. **Handle authentication** with private key
3. **Use client methods** instead of direct HTTP calls
4. **Keep our Market model** but populate from ClobClient responses

## Example: Fetching Markets with py-clob-client

```python
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Initialize
client = ClobClient(
    api_url="https://clob.polymarket.com",
    chain_id=POLYGON,
    private_key=settings.polymarket_private_key
)

# Get all markets
markets = client.get_markets()

# Get specific market
market = client.get_market(market_id)

# Get orderbook
orderbook = client.get_orderbook(market_id)
```

## Authentication

You'll need:
- **Private Key**: Your wallet's private key for signing transactions
- **Chain ID**: POLYGON (for mainnet) or MUMBAI (for testnet)

Add to `.env`:
```bash
POLYMARKET_PRIVATE_KEY=your_private_key_here
```

⚠️ **Security Note**: Never commit your private key to git. Always use `.env` file.

## Next Steps

1. **Review py-clob-client docs**: Check the GitHub README
2. **Get a test private key**: Use a test wallet for development
3. **Update our code**: Migrate to use ClobClient
4. **Test with testnet**: Use testnet first before mainnet

## Resources

- **GitHub**: https://github.com/Polymarket/py-clob-client
- **Agents Example**: https://github.com/Polymarket/agents (great reference)
- **Documentation**: https://docs.polymarket.com
- **CLOB API Docs**: Check py-clob-client repository

## Benefits of Using py-clob-client

1. ✅ **Official Support**: Maintained by Polymarket team
2. ✅ **Proper Auth**: Handles authentication correctly
3. ✅ **Type Safety**: Better error handling
4. ✅ **Active Development**: Regularly updated
5. ✅ **Community**: Large user base (632 stars)
6. ✅ **Examples**: Agents repo shows best practices


