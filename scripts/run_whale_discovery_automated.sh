#!/bin/bash
# Automated Whale Discovery Script
# This script handles the Railway tunnel setup and runs whale discovery automatically

set -e  # Exit on error

echo "======================================================================"
echo "  AUTOMATED WHALE DISCOVERY SETUP"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found${NC}"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

# Check if we're in the project directory
if [ ! -f "scripts/init_whale_discovery.py" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI found${NC}"
echo ""

# Step 1: Check if tunnel is already running
echo "Step 1: Checking for existing Railway tunnel..."
TUNNEL_PID=$(pgrep -f "railway connect postgres" || true)

if [ -n "$TUNNEL_PID" ]; then
    echo -e "${YELLOW}⚠️  Found existing tunnel (PID: $TUNNEL_PID)${NC}"
    echo "   Using existing tunnel..."
else
    echo "   No existing tunnel found"
    echo ""
    echo -e "${YELLOW}⚠️  This script will create a Railway database tunnel${NC}"
    echo "   The tunnel will run in the background"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    echo ""
    
    # Start tunnel in background
    echo "Creating Railway tunnel..."
    railway connect postgres &
    TUNNEL_PID=$!
    
    # Wait a moment for tunnel to establish
    sleep 3
    
    echo -e "${GREEN}✅ Tunnel started (PID: $TUNNEL_PID)${NC}"
    echo "   (You can stop it later with: kill $TUNNEL_PID)"
    echo ""
fi

# Step 2: Get the tunneled connection string
echo "Step 2: Getting tunneled database connection..."
echo "   (This may take a moment...)"

# Try to get the connection string from Railway
# Note: Railway might expose this differently, so we'll try a few methods
TUNNELED_URL=""

# Method 1: Check if Railway exposes a local connection
# Railway tunnel typically creates a local connection on localhost
# We'll construct it from environment variables if possible

# Get DATABASE_URL from Railway
RAILWAY_DB_URL=$(railway variables --service web DATABASE_URL 2>/dev/null || echo "")

if [ -n "$RAILWAY_DB_URL" ]; then
    # Convert Railway internal URL to localhost
    # postgresql://user:pass@postgres.railway.internal:5432/db
    # becomes: postgresql://user:pass@localhost:5432/db
    TUNNELED_URL=$(echo "$RAILWAY_DB_URL" | sed 's/postgres\.railway\.internal/localhost/g')
    echo -e "${GREEN}✅ Found database URL${NC}"
else
    echo -e "${YELLOW}⚠️  Could not automatically detect tunneled URL${NC}"
    echo ""
    echo "Please provide the tunneled connection string:"
    echo "Format: postgresql://postgres:PASSWORD@localhost:PORT/railway"
    read -p "DATABASE_URL: " TUNNELED_URL
fi

if [ -z "$TUNNELED_URL" ]; then
    echo -e "${RED}❌ No database URL provided${NC}"
    exit 1
fi

echo ""

# Step 3: Run the whale discovery script
echo "Step 3: Running whale discovery..."
echo ""

export DATABASE_URL="$TUNNELED_URL"
python scripts/init_whale_discovery.py

DISCOVERY_EXIT_CODE=$?

echo ""
echo "======================================================================"
if [ $DISCOVERY_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Whale discovery completed successfully!${NC}"
else
    echo -e "${RED}❌ Whale discovery failed (exit code: $DISCOVERY_EXIT_CODE)${NC}"
fi
echo "======================================================================"
echo ""

# Step 4: Cleanup reminder
if [ -n "$TUNNEL_PID" ] && [ -z "$(pgrep -f "railway connect postgres" | grep -v "^$TUNNEL_PID$")" ]; then
    echo "Note: The Railway tunnel is still running (PID: $TUNNEL_PID)"
    echo "To stop it, run: kill $TUNNEL_PID"
    echo ""
fi

exit $DISCOVERY_EXIT_CODE

