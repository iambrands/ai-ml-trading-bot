#!/bin/bash
# Simple script to import SQL file to Railway PostgreSQL

set -e

SQL_FILE="local_db_backup_railway.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found!"
    exit 1
fi

echo "📦 Importing database to Railway PostgreSQL..."
echo "File: $SQL_FILE"
echo "Size: $(du -h "$SQL_FILE" | cut -f1)"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI not found!"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if project is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Project not linked. Linking now..."
    echo "   (This might prompt you to select a project)"
    railway link
fi

# Check if service is linked
if railway service &> /dev/null | grep -q "No service linked"; then
    echo "⚠️  Service not linked. Linking PostgreSQL service..."
    echo "   (You'll need to select 'Postgres' when prompted)"
    echo "Postgres" | railway service || railway service
fi

echo "🔍 Getting DATABASE_URL from Railway..."
DATABASE_URL=$(railway variables get DATABASE_URL 2>/dev/null || railway variables 2>/dev/null | grep DATABASE_URL | head -1 | awk '{print $NF}')

if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not found in variables. Trying alternative method..."
    echo ""
    echo "📋 Please get DATABASE_URL manually from Railway dashboard:"
    echo "   1. Go to Railway dashboard"
    echo "   2. Select your PostgreSQL service"
    echo "   3. Go to Variables tab"
    echo "   4. Copy the DATABASE_URL value"
    echo ""
    echo "Then run:"
    echo "   psql \"DATABASE_URL\" -f local_db_backup_railway.sql"
    echo ""
    echo "OR provide connection details manually..."
    echo ""
    read -p "Enter DATABASE_URL (or press Enter to exit): " DATABASE_URL
    
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ DATABASE_URL not provided. Exiting."
        exit 1
    fi
fi

echo "✅ Connection details found"
echo ""

# Check if psql is installed locally
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql not found locally!"
    echo "Please install PostgreSQL client tools: brew install postgresql"
    exit 1
fi

echo "✅ psql found locally"
echo ""
echo "🚀 Starting import..."
echo ""

# Import the SQL file directly using DATABASE_URL
# psql can accept DATABASE_URL directly with -d flag
psql "$DATABASE_URL" -f "$SQL_FILE"

echo ""
echo "✅ Import complete!"
echo ""
echo "Verifying import..."
echo ""

# Verify the import
psql "$DATABASE_URL" -c "SELECT COUNT(*) as markets_count FROM markets;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as predictions_count FROM predictions;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as signals_count FROM signals;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as trades_count FROM trades;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"

echo ""
echo "✅ Done!"

