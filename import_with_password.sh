#!/bin/bash
# Import database with Railway PostgreSQL credentials

set -e

HOST="shuttle.proxy.rlwy.net"
USER="postgres"
PASSWORD="zTgqDKjcBkQcoyOhQsJAtmEWwigkXuMu"
DB="railway"
SQL_FILE="local_db_backup_railway.sql"

echo "📋 Railway Database Import"
echo "=========================="
echo ""
echo "Host: $HOST"
echo "User: $USER"
echo "Database: $DB"
echo ""

read -p "Enter TCP Proxy Port (from Railway Dashboard): " PORT

if [ -z "$PORT" ]; then
    echo "❌ Error: Port is required"
    echo ""
    echo "💡 Check Railway Dashboard → Postgres → Deployments tab for port number"
    exit 1
fi

DATABASE_URL="postgresql://${USER}:${PASSWORD}@${HOST}:${PORT}/${DB}"

echo ""
echo "✅ Constructed DATABASE_URL:"
echo "   postgresql://${USER}:***@${HOST}:${PORT}/${DB}"
echo ""

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found"
    exit 1
fi

echo "📦 SQL file ready: $SQL_FILE ($(wc -l < "$SQL_FILE") lines)"
echo ""

read -p "Ready to import? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Import cancelled."
    exit 0
fi

echo ""
echo "🔄 Testing connection first..."
if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Connection successful!"
else
    echo "❌ Connection failed. Check:"
    echo "   - Port number is correct"
    echo "   - Service is Online in Railway"
    echo "   - Password is correct"
    exit 1
fi

echo ""
echo "🔄 Importing database..."
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
    echo "   Connection: postgresql://${USER}:***@${HOST}:${PORT}/${DB}"
else
    echo ""
    echo "❌ Import failed (exit code: $EXIT_CODE)"
    exit 1
fi
