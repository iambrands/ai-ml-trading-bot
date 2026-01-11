#!/bin/bash
# Import database using known Railway values

set -e

# Known values from Railway
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="zTgqDKjcBkQcoyOhQsJAtmEWwigkXuMu"
POSTGRES_DB="railway"

echo "📋 Railway PostgreSQL Import"
echo ""
echo "We have:"
echo "  User: $POSTGRES_USER"
echo "  Password: [hidden]"
echo "  Database: $POSTGRES_DB"
echo ""

# Try to get TCP_PROXY values from Railway CLI
echo "🔍 Attempting to get TCP_PROXY values from Railway..."
TCP_DOMAIN=$(railway variables get RAILWAY_TCP_PROXY_DOMAIN 2>/dev/null | grep -v "No service linked" | tail -1 || echo "")
TCP_PORT=$(railway variables get RAILWAY_TCP_PROXY_PORT 2>/dev/null | grep -v "No service linked" | tail -1 || echo "")

if [ -z "$TCP_DOMAIN" ] || [ -z "$TCP_PORT" ]; then
    echo "⚠️  Could not get TCP_PROXY values automatically."
    echo ""
    echo "Please check Railway Dashboard → PostgreSQL → Variables tab"
    echo "and look for the ACTUAL values (not templates) of:"
    echo "  - RAILWAY_TCP_PROXY_DOMAIN"
    echo "  - RAILWAY_TCP_PROXY_PORT"
    echo ""
    read -p "RAILWAY_TCP_PROXY_DOMAIN: " TCP_DOMAIN
    read -p "RAILWAY_TCP_PROXY_PORT: " TCP_PORT
fi

if [ -z "$TCP_DOMAIN" ] || [ -z "$TCP_PORT" ]; then
    echo "❌ Error: TCP_PROXY values are required!"
    echo ""
    echo "Alternative: Check if Railway provides a 'Public Network' connection string"
    echo "in the Connect modal, or check the Variables tab for actual resolved values."
    exit 1
fi

# Construct public connection string
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${TCP_DOMAIN}:${TCP_PORT}/${POSTGRES_DB}"

echo ""
echo "✅ Constructed connection string:"
echo "   postgresql://${POSTGRES_USER}:***@${TCP_DOMAIN}:${TCP_PORT}/${POSTGRES_DB}"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql not found!"
    echo "Install with: brew install postgresql"
    exit 1
fi

echo "🚀 Testing connection..."
if psql "$DATABASE_URL" -c "SELECT version();" &> /dev/null; then
    echo "✅ Connection successful!"
    echo ""
    echo "📦 Importing database..."
    psql "$DATABASE_URL" -f local_db_backup_railway_clean.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Import successful!"
        echo ""
        echo "Verifying import..."
        echo ""
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as markets_count FROM markets;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as predictions_count FROM predictions;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as signals_count FROM signals;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as trades_count FROM trades;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"
        echo ""
        echo "✅ Done!"
    else
        echo ""
        echo "❌ Import failed. Check the error messages above."
        exit 1
    fi
else
    echo "❌ Connection failed!"
    echo ""
    echo "Please verify:"
    echo "  1. TCP_PROXY_DOMAIN and TCP_PROXY_PORT are correct"
    echo "  2. PostgreSQL service is online"
    echo "  3. Your IP is allowed (if Railway has IP restrictions)"
    exit 1
fi


