#!/bin/bash
# Run database migration for alerts and paper trading on Railway

set -e

echo "🔧 Running Database Migration for Alerts & Paper Trading"
echo "=========================================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "To get your DATABASE_URL from Railway:"
    echo "1. Go to Railway dashboard"
    echo "2. Select your PostgreSQL service"
    echo "3. Go to Variables tab"
    echo "4. Copy the DATABASE_URL value"
    echo ""
    echo "Or use Railway CLI:"
    echo "  railway variables"
    echo ""
    echo "Then set it:"
    echo "  export DATABASE_URL='your-connection-string'"
    echo ""
    exit 1
fi

echo "✅ DATABASE_URL found"
echo ""

# Migration file path
MIGRATION_FILE="src/database/migrations/add_alerts_and_paper_trading.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ ERROR: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "📄 Migration file: $MIGRATION_FILE"
echo ""

# Run migration using psql
echo "🚀 Running migration..."
echo ""

psql "$DATABASE_URL" -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "New tables/columns added:"
    echo "  - alerts table"
    echo "  - alert_history table"
    echo "  - analytics_cache table"
    echo "  - paper_trading column on trades"
    echo "  - paper_trading column on portfolio_snapshots"
    echo ""
else
    echo ""
    echo "❌ Migration failed. Check the error above."
    exit 1
fi


