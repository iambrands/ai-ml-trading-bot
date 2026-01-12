#!/bin/bash
# Run database migration for alerts and paper trading

set -e

echo "🚀 Running database migration for alerts and paper trading..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set. Please set it or use Railway CLI:"
    echo "   railway connect postgres"
    exit 1
fi

# Run migration
psql "$DATABASE_URL" -f src/database/migrations/add_alerts_and_paper_trading.sql

echo "✅ Migration completed successfully!"
echo ""
echo "New tables created:"
echo "  - alerts"
echo "  - alert_history"
echo "  - analytics_cache"
echo ""
echo "Columns added:"
echo "  - trades.paper_trading"
echo "  - portfolio_snapshots.paper_trading"


