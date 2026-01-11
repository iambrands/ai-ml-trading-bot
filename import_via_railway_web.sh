#!/bin/bash
# Import database to Railway PostgreSQL
# This script helps construct the connection string from individual variables

echo "📋 Railway Database Import Helper"
echo "================================"
echo ""

echo "Since DATABASE_URL is empty, we need to use individual variables."
echo ""
echo "Please go to Railway Dashboard → Postgres → Variables tab and find these:"
echo ""

echo "1. POSTGRES_USER or PGUSER (usually: postgres)"
read -p "   Enter POSTGRES_USER: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-postgres}

echo ""
echo "2. POSTGRES_PASSWORD or PGPASSWORD (Railway auto-generates this)"
echo "   This should be a long random string"
read -p "   Enter POSTGRES_PASSWORD: " POSTGRES_PASSWORD

echo ""
echo "3. POSTGRES_HOST or PGHOST"
echo "   Could be: postgres.railway.internal (internal) or interchange.proxy.rlwy.net (public)"
read -p "   Enter POSTGRES_HOST: " POSTGRES_HOST

echo ""
echo "4. POSTGRES_PORT or PGPORT (usually: 5432 or 13955)"
read -p "   Enter POSTGRES_PORT: " POSTGRES_PORT
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo ""
echo "5. POSTGRES_DB or PGDATABASE (usually: railway or postgres)"
read -p "   Enter POSTGRES_DB: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-railway}

echo ""
echo "================================"
echo "Constructing DATABASE_URL..."
echo ""

if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_HOST" ]; then
    echo "❌ Error: POSTGRES_PASSWORD and POSTGRES_HOST are required"
    echo ""
    echo "💡 Tip: Check Railway Dashboard → Postgres → Variables tab for these values"
    exit 1
fi

DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

echo "✅ Constructed DATABASE_URL:"
echo "   postgresql://${POSTGRES_USER}:***@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo ""

# Check if SQL file exists
SQL_FILE="local_db_backup_railway.sql"
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found"
    exit 1
fi

echo "📦 SQL file found: $SQL_FILE ($(wc -l < "$SQL_FILE") lines)"
echo ""

read -p "Ready to import? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Import cancelled."
    exit 0
fi

echo ""
echo "🔄 Importing database..."
echo ""

psql "$DATABASE_URL" < "$SQL_FILE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
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
    " 2>&1
    
    echo ""
    echo "✅ Done! Your database has been imported to Railway."
    echo "   Your web service should now access this data automatically."
else
    echo ""
    echo "❌ Import failed (exit code: $EXIT_CODE)"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   - Check that all values are correct"
    echo "   - Verify PostgreSQL service is running in Railway"
    echo "   - Check that host is accessible (use public URL if internal doesn't work)"
    echo "   - Try using Railway CLI: railway connect postgres"
    exit 1
fi


