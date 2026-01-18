#!/bin/bash
# Run migration on Railway

set -e  # Exit on error

echo "🚀 Running database migration on Railway..."
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    echo ""
    echo "Get it from Railway:"
    echo "1. Go to Railway Dashboard"
    echo "2. Click Postgres service"
    echo "3. Click Variables tab"
    echo "4. Copy DATABASE_URL value"
    echo ""
    echo "Then run:"
    echo "  export DATABASE_URL='postgresql://...'"
    echo "  ./scripts/run_migration.sh"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 not found"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "📦 Installing psycopg2-binary..."
    pip install psycopg2-binary --quiet
    echo ""
fi

# Run migration
python3 scripts/run_migration.py

echo ""
echo "✅ Migration complete!"
