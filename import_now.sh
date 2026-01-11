#!/bin/bash
# Import database using the public connection string

set -e

# Connection details
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="zTgqDKjcBkQcoyOhQsJAtmEWwigkXuMu"
POSTGRES_DB="railway"
TCP_DOMAIN="shuttle.proxy.rlwy.net"
TCP_PORT="46223"

DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${TCP_DOMAIN}:${TCP_PORT}/${POSTGRES_DB}"

echo "📦 Importing database to Railway PostgreSQL..."
echo ""
echo "Connection: postgresql://${POSTGRES_USER}:***@${TCP_DOMAIN}:${TCP_PORT}/${POSTGRES_DB}"
echo ""

# Test connection first
echo "🔍 Testing connection..."
if psql "$DATABASE_URL" -c "SELECT version();" &> /dev/null; then
    echo "✅ Connection successful!"
    echo ""
    echo "📥 Importing SQL file..."
    psql "$DATABASE_URL" -f local_db_backup_railway_clean.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Import successful!"
        echo ""
        echo "📊 Verifying import..."
        echo ""
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as markets_count FROM markets;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as predictions_count FROM predictions;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as signals_count FROM signals;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as trades_count FROM trades;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"
        echo ""
        echo "✅ Database import complete!"
    else
        echo ""
        echo "❌ Import failed. Check the error messages above."
        exit 1
    fi
else
    echo "❌ Connection failed!"
    echo "Please verify the connection details."
    exit 1
fi
