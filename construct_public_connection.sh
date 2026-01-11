#!/bin/bash
# Script to construct public PostgreSQL connection string for Railway

echo "📋 Railway PostgreSQL Public Connection Builder"
echo ""
echo "Please provide the following from Railway Dashboard → PostgreSQL → Variables:"
echo ""

read -p "RAILWAY_TCP_PROXY_DOMAIN: " TCP_DOMAIN
read -p "RAILWAY_TCP_PROXY_PORT: " TCP_PORT
read -p "POSTGRES_PASSWORD: " PASSWORD
read -p "POSTGRES_USER [postgres]: " USER
USER=${USER:-postgres}
read -p "POSTGRES_DB [railway]: " DB
DB=${DB:-railway}

if [ -z "$TCP_DOMAIN" ] || [ -z "$TCP_PORT" ] || [ -z "$PASSWORD" ]; then
    echo "❌ Error: Missing required values!"
    exit 1
fi

DATABASE_URL="postgresql://${USER}:${PASSWORD}@${TCP_DOMAIN}:${TCP_PORT}/${DB}"

echo ""
echo "✅ Public Connection String:"
echo "$DATABASE_URL"
echo ""
echo "📋 To import the database, run:"
echo "   psql \"$DATABASE_URL\" -f local_db_backup_railway_clean.sql"
echo ""
echo "🚀 Ready to import? (y/n)"
read -r response

if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    echo ""
    echo "📦 Importing database..."
    psql "$DATABASE_URL" -f local_db_backup_railway_clean.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Import successful!"
        echo ""
        echo "Verifying import..."
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as markets_count FROM markets;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as predictions_count FROM predictions;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as signals_count FROM signals;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as trades_count FROM trades;"
        psql "$DATABASE_URL" -c "SELECT COUNT(*) as portfolio_count FROM portfolio_snapshots;"
    else
        echo ""
        echo "❌ Import failed. Check the error messages above."
    fi
else
    echo ""
    echo "Connection string saved. Run the import command manually when ready."
fi

