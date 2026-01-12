#!/bin/bash
# Run database migration on Railway

echo "🚀 Running Database Migration on Railway"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo ""
    echo "To get your Railway DATABASE_URL:"
    echo "1. Go to Railway dashboard"
    echo "2. Select your PostgreSQL service"
    echo "3. Go to 'Variables' tab"
    echo "4. Copy the DATABASE_URL value"
    echo ""
    echo "Then run:"
    echo "  export DATABASE_URL='your-railway-database-url'"
    echo "  ./scripts/run_migration_railway.sh"
    echo ""
    echo "OR use Railway CLI:"
    echo "  railway connect postgres"
    echo "  Then run: \\i src/database/migrations/002_performance_indexes.sql"
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo "📝 Running migration: src/database/migrations/002_performance_indexes.sql"
echo ""

# Run the migration
psql "$DATABASE_URL" -f src/database/migrations/002_performance_indexes.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo "📊 Database indexes have been added"
else
    echo ""
    echo "❌ Migration failed. Check the error above."
    exit 1
fi
