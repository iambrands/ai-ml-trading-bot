#!/bin/bash
# Quick script to import database to Railway PostgreSQL
# Usage: ./import_to_railway.sh "postgresql://user:pass@host:port/dbname"

set -e

if [ -z "$1" ]; then
    echo "❌ Error: DATABASE_URL required"
    echo ""
    echo "Usage: $0 \"postgresql://user:pass@host:port/dbname\""
    echo ""
    echo "To get your DATABASE_URL:"
    echo "1. Go to Railway dashboard: https://railway.app"
    echo "2. Select your project: handsome-perception"
    echo "3. Click on your PostgreSQL service"
    echo "4. Go to 'Variables' tab"
    echo "5. Copy the DATABASE_URL value"
    echo ""
    exit 1
fi

DATABASE_URL="$1"
SQL_FILE="local_db_backup_railway.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found"
    exit 1
fi

echo "📦 Importing database to Railway..."
echo "📁 SQL file: $SQL_FILE"
echo "🔗 Database: ${DATABASE_URL%%@*}@***"
echo ""

# Import the database
psql "$DATABASE_URL" < "$SQL_FILE"

echo ""
echo "✅ Database import completed!"
echo ""
echo "🔍 Verifying import..."
psql "$DATABASE_URL" -c "
SELECT 
    'markets' as table_name, COUNT(*) as rows FROM markets
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'trades', COUNT(*) FROM trades
UNION ALL
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots;
"

echo ""
echo "✅ Done! Your database has been imported to Railway."
echo "   Your web service should now connect automatically using DATABASE_URL."



