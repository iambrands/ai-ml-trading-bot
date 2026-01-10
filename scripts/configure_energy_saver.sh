#!/bin/bash
# Configure Energy Saver settings to prevent sleep

echo "⚙️  Configuring Energy Saver settings..."
echo ""

# Check if running as root (needed for system-wide settings)
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs admin privileges for system-wide settings"
    echo "   Running user-level configuration instead..."
    echo ""
    echo "📝 Manual steps for system-wide settings:"
    echo "   1. System Preferences → Energy Saver"
    echo "   2. Set 'Computer sleep' to 'Never'"
    echo "   3. Uncheck 'Put hard disks to sleep when possible'"
    echo "   4. Set 'Display sleep' to desired time (doesn't affect training)"
    echo ""
fi

# User-level: Use pmset (works without admin)
echo "🔧 Setting user-level power management..."

# Prevent sleep when display is off (for current user)
pmset -c sleep 0 2>/dev/null || echo "   Note: Some settings require admin privileges"

# Prevent idle sleep
pmset -c disablesleep 1 2>/dev/null || echo "   Note: Some settings require admin privileges"

# Prevent disk sleep
pmset -c disksleep 0 2>/dev/null || echo "   Note: Some settings require admin privileges"

echo ""
echo "✅ Configuration applied!"
echo ""
echo "📊 Current power settings:"
pmset -g

echo ""
echo "💡 To make permanent system-wide changes:"
echo "   sudo pmset -a sleep 0"
echo "   sudo pmset -a disablesleep 1"
echo "   sudo pmset -a disksleep 0"

