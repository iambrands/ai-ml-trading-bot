#!/bin/bash
# Database setup script for Polymarket AI Trading Bot

set -e

echo "🗄️  Polymarket AI Trading Bot - Database Setup"
echo "================================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed."
    echo ""
    echo "To install PostgreSQL on macOS:"
    echo "  brew install postgresql@14"
    echo "  brew services start postgresql@14"
    echo ""
    echo "Or visit: https://www.postgresql.org/download/"
    exit 1
fi

echo "✅ PostgreSQL is installed"
psql --version
echo ""

# Check if PostgreSQL is running
if ! pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL is not running."
    echo ""
    echo "To start PostgreSQL:"
    echo "  brew services start postgresql@14"
    echo "  # or"
    echo "  pg_ctl -D /usr/local/var/postgres start"
    echo ""
    read -p "Do you want to try starting it now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null || echo "Could not start automatically. Please start manually."
        fi
        sleep 2
        if ! pg_isready &> /dev/null; then
            echo "❌ Could not start PostgreSQL. Please start it manually."
            exit 1
        fi
    else
        exit 1
    fi
fi

echo "✅ PostgreSQL is running"
echo ""

# Get database configuration
read -p "Database name [polymarket_trader]: " DB_NAME
DB_NAME=${DB_NAME:-polymarket_trader}

read -p "Database user [postgres]: " DB_USER
DB_USER=${DB_USER:-postgres}

read -p "Database password (leave empty if no password): " -s DB_PASSWORD
echo ""

read -p "Database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Database port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo ""
echo "Creating database and user..."

# Create database and user
psql postgres <<EOF
-- Create database if it doesn't exist
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Create user if it doesn't exist (if password provided)
EOF

if [ -n "$DB_PASSWORD" ]; then
    psql postgres <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
else
    echo "Using existing user: $DB_USER"
fi

echo "✅ Database and user created"
echo ""

# Update .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Update database settings in .env
if grep -q "POSTGRES_" "$ENV_FILE"; then
    echo "Updating existing database settings in .env file..."
    sed -i.bak "s|POSTGRES_HOST=.*|POSTGRES_HOST=$DB_HOST|" "$ENV_FILE"
    sed -i.bak "s|POSTGRES_PORT=.*|POSTGRES_PORT=$DB_PORT|" "$ENV_FILE"
    sed -i.bak "s|POSTGRES_DB=.*|POSTGRES_DB=$DB_NAME|" "$ENV_FILE"
    sed -i.bak "s|POSTGRES_USER=.*|POSTGRES_USER=$DB_USER|" "$ENV_FILE"
    if [ -n "$DB_PASSWORD" ]; then
        sed -i.bak "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASSWORD|" "$ENV_FILE"
    fi
    rm -f "$ENV_FILE.bak"
else
    echo "Adding database settings to .env file..."
    cat >> "$ENV_FILE" <<EOF

# Database Configuration
POSTGRES_HOST=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
EOF
fi

echo "✅ .env file updated"
echo ""

# Initialize database schema
echo "Initializing database schema..."
if [ -n "$DB_PASSWORD" ]; then
    export PGPASSWORD="$DB_PASSWORD"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f src/database/schema.sql
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f src/database/schema.sql
fi

echo "✅ Database schema initialized"
echo ""

# Test connection
echo "Testing database connection..."
python3 <<EOF
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db

async def test():
    try:
        async for db in get_db():
            print("✅ Database connection successful!")
            break
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

asyncio.run(test())
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Database setup complete!"
    echo ""
    echo "You can now:"
    echo "  1. Restart the API server"
    echo "  2. Use the UI to view data"
    echo "  3. Train models (data will be saved to database)"
else
    echo ""
    echo "⚠️  Database connection test failed. Please check your settings."
    exit 1
fi



