#!/bin/bash
# Import SQL file to Railway PostgreSQL using Railway CLI

set -e

SQL_FILE="local_db_backup_railway.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found!"
    exit 1
fi

echo "📦 Importing database to Railway PostgreSQL..."
echo ""
echo "File: $SQL_FILE"
echo "Size: $(du -h "$SQL_FILE" | cut -f1)"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI not found!"
    echo "Install it from: https://docs.railway.app/develop/cli"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Error: Not logged into Railway!"
    echo "Run: railway login"
    exit 1
fi

echo "✅ Railway CLI found and logged in"
echo ""

# Check if project is linked
if ! railway status &> /dev/null; then
    echo "⚠️  Project not linked. Linking now..."
    railway link
fi

echo "🔍 Getting Railway PostgreSQL connection details..."
echo ""

# Method 1: Use railway connect postgres (interactive, but we'll pipe to it)
# Actually, railway connect opens an interactive shell, so that won't work

# Method 2: Use railway run with service selection via environment
# But this still prompts for service

# Method 3: Use railway variables to get DATABASE_URL and use psql directly
echo "📋 Getting DATABASE_URL from Railway..."
DATABASE_URL=$(railway variables --json 2>/dev/null | grep -o '"DATABASE_URL":"[^"]*"' | cut -d'"' -f4 || railway variables | grep DATABASE_URL | awk '{print $2}')

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not found in variables. Trying alternative method..."
    echo ""
    echo "📋 You'll need to select the PostgreSQL service manually."
    echo "   This will prompt you to choose between 'web' and 'Postgres'."
    echo "   Please select 'Postgres' when prompted."
    echo ""
    echo "🚀 Starting import (you'll be prompted for service selection)..."
    echo ""
    
    # Use railway run with psql, but pipe the SQL file
    # Note: This might still fail due to interactive prompts
    cat "$SQL_FILE" | railway run psql 2>&1 || {
        echo ""
        echo "⚠️  Import failed. Trying to use railway connect postgres..."
        echo ""
        echo "📋 Alternative method: Manual import"
        echo ""
        echo "1. Run: railway connect postgres"
        echo "2. Once connected, type: \\i local_db_backup_railway.sql"
        echo "   (Note: The file needs to be accessible from Railway's environment)"
        echo ""
        echo "OR use this method instead:"
        echo ""
        echo "   railway run bash -c 'cat > /tmp/import.sql' < $SQL_FILE"
        echo "   railway run psql -f /tmp/import.sql"
        echo ""
        exit 1
    }
else
    echo "✅ Found DATABASE_URL"
    echo "🚀 Importing using direct psql connection..."
    echo ""
    
    # Convert DATABASE_URL to psql format if needed
    # Railway's DATABASE_URL is usually: postgresql://user:pass@host:port/db
    if echo "$DATABASE_URL" | grep -q "postgresql://"; then
        # Use psql directly with DATABASE_URL
        export PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        export PGHOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        export PGPORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        export PGUSER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        export PGDATABASE=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
        
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$SQL_FILE"
    else
        echo "❌ Invalid DATABASE_URL format"
        exit 1
    fi
fi

echo ""
echo "✅ Import complete!"
echo ""
echo "Verifying import..."
echo ""

# Verify the import
if [ -n "$DATABASE_URL" ]; then
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT COUNT(*) as markets_count FROM markets;"
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT COUNT(*) as predictions_count FROM predictions;"
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT COUNT(*) as signals_count FROM signals;"
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT COUNT(*) as trades_count FROM trades;"
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"
else
    railway run psql -c "SELECT COUNT(*) as markets_count FROM markets;"
    railway run psql -c "SELECT COUNT(*) as predictions_count FROM predictions;"
    railway run psql -c "SELECT COUNT(*) as signals_count FROM signals;"
    railway run psql -c "SELECT COUNT(*) as trades_count FROM trades;"
    railway run psql -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"
fi

echo ""
echo "✅ Done!"

