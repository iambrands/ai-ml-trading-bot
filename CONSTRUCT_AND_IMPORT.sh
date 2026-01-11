#!/bin/bash
# Construct DATABASE_URL from Railway public URL and individual variables
# Then import the database

set -e

echo "📋 Railway Database Import"
echo "=========================="
echo ""

# We have: postgresql://:@interchange.proxy.rlwy.net:13955/
HOST="interchange.proxy.rlwy.net"
PORT="13955"

echo "✅ Connection details found:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""

echo "We need the password from Railway."
echo "Please go to Railway Dashboard → Postgres → Variables tab and find:"
echo "   POSTGRES_PASSWORD or PGPASSWORD"
echo ""

read -p "Enter POSTGRES_PASSWORD: " PASSWORD

if [ -z "$PASSWORD" ]; then
    echo ""
    echo "❌ Error: Password is required"
    echo ""
    echo "💡 Tip: Check Railway Dashboard → Postgres → Variables tab"
    echo "   Look for POSTGRES_PASSWORD or PGPASSWORD"
    echo "   Railway auto-generates this when PostgreSQL service is created"
    exit 1
fi

# Default values for Railway PostgreSQL
# Railway might use 'postgres' or 'railway' as default user
echo ""
echo "Railway CLI tried to use user 'iabadvisors' - we need 'postgres' instead."
echo ""
read -p "Enter PostgreSQL username (default: postgres): " USER
USER=${USER:-postgres}

read -p "Enter PostgreSQL database name (default: railway): " DB
DB=${DB:-railway}

echo ""
echo "Using:"
echo "   Username: $USER"
echo "   Database: $DB"
echo ""

# Construct full connection string
DATABASE_URL="postgresql://${USER}:${PASSWORD}@${HOST}:${PORT}/${DB}"

echo "✅ Constructed DATABASE_URL:"
echo "   postgresql://${USER}:***@${HOST}:${PORT}/${DB}"
echo ""

# Check if SQL file exists
SQL_FILE="local_db_backup_railway.sql"
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
    echo "❌ Connection failed. Please check:"
    echo "   - Password is correct"
    echo "   - Host and port are accessible"
    echo "   - Database name might be different (try 'postgres' instead of 'railway')"
    echo ""
    read -p "Try with database 'postgres' instead? (y/n): " try_postgres
    if [ "$try_postgres" = "y" ] || [ "$try_postgres" = "Y" ]; then
        DB="postgres"
        DATABASE_URL="postgresql://${USER}:${PASSWORD}@${HOST}:${PORT}/${DB}"
        echo "Retrying with database 'postgres'..."
        if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
            echo "✅ Connection successful with 'postgres' database!"
        else
            echo "❌ Still failed. Please check Railway variables manually."
            exit 1
        fi
    else
        exit 1
    fi
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
    echo "   Connection string: postgresql://${USER}:***@${HOST}:${PORT}/${DB}"
    echo "   Your web service should now access this data automatically."
else
    echo ""
    echo "❌ Import failed (exit code: $EXIT_CODE)"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   - Check Railway logs for PostgreSQL service"
    echo "   - Verify password is correct"
    echo "   - Try different database name (postgres, railway)"
    echo "   - Check that tables don't already exist (might need to drop first)"
    exit 1
fi

