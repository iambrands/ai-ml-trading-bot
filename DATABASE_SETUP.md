# Database Setup (Optional)

The API and UI work **without a database**, but setting up PostgreSQL enables data persistence and historical tracking.

## Quick Start Without Database

The UI and API endpoints will work fine without PostgreSQL - they'll just return empty results. This is perfect for:
- Testing the UI
- Training models (doesn't require DB)
- Viewing the interface

## Setting Up PostgreSQL (Optional)

If you want to persist data, follow these steps:

### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database and User

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE polymarket_trader;

# Create user (optional - can use default postgres user)
CREATE USER polymarket_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE polymarket_trader TO polymarket_user;

# Exit
\q
```

### 3. Update .env File

Add to your `.env` file:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=polymarket_trader
POSTGRES_USER=postgres  # or your custom user
POSTGRES_PASSWORD=your_password
```

### 4. Initialize Database Schema

```bash
python scripts/init_db.py
```

Or manually:

```bash
psql -U postgres -d polymarket_trader -f src/database/schema.sql
```

## Current Status

✅ **API works without database** - Returns empty results gracefully
✅ **UI works without database** - Shows "No data" messages
✅ **Training works without database** - Models save to files
✅ **Database optional** - Can be set up later

## Troubleshooting

### "role postgres does not exist"

This means PostgreSQL isn't set up. **This is OK!** The API will work without it.

To fix (if you want database):
1. Install PostgreSQL
2. Create the postgres user: `createuser -s postgres`
3. Or use a different user in `.env`

### "Connection refused"

PostgreSQL isn't running. Start it:
```bash
# macOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql
```

### Database Not Required

Remember: **You don't need a database to:**
- ✅ View the UI
- ✅ Train models
- ✅ Test the API
- ✅ Run backtests

Database is only needed for:
- Persisting trade history
- Storing predictions
- Portfolio tracking over time


