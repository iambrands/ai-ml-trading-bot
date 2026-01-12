# Prevent Mac from Sleeping - Complete Guide

## Quick Start

### Method 1: Automatic (Recommended)

```bash
# Start training with sleep prevention
./scripts/run_training_server.sh
./scripts/prevent_sleep.sh
```

This will:
- Start training
- Automatically prevent sleep while training runs
- Stop sleep prevention when training completes

### Method 2: Manual

```bash
# Prevent sleep indefinitely
caffeinate -d

# Or prevent sleep for specific duration (e.g., 8 hours)
caffeinate -d -t 28800
```

## Methods Explained

### Method 1: caffeinate (Temporary - Until Reboot)

**Prevent sleep while training runs:**
```bash
# If training is running
caffeinate -w $(cat .training.pid)

# Or use the script
./scripts/prevent_sleep.sh
```

**Prevent sleep indefinitely:**
```bash
caffeinate -d
```

**Prevent sleep for specific time:**
```bash
# 8 hours
caffeinate -d -t 28800

# 24 hours
caffeinate -d -t 86400
```

**Stop caffeinate:**
```bash
# Find and kill
pkill caffeinate

# Or use script
./scripts/stop_prevent_sleep.sh
```

### Method 2: System Settings (Permanent)

**Via System Preferences:**
1. Open **System Preferences** → **Energy Saver** (or **Battery** on newer macOS)
2. Set **"Computer sleep"** to **"Never"**
3. Uncheck **"Put hard disks to sleep when possible"**
4. Set **"Display sleep"** to desired time (doesn't affect training)

**Via Command Line (requires admin):**
```bash
# Prevent sleep completely
sudo pmset -a sleep 0

# Prevent idle sleep
sudo pmset -a disablesleep 1

# Prevent disk sleep
sudo pmset -a disksleep 0

# View current settings
pmset -g
```

**Run configuration script:**
```bash
./scripts/configure_energy_saver.sh
```

### Method 3: launchd Service (Automatic on Boot)

Create a launchd service that prevents sleep automatically:

```bash
# Copy plist to LaunchAgents
cp com.polymarket.training.plist ~/Library/LaunchAgents/

# Load service
launchctl load ~/Library/LaunchAgents/com.polymarket.training.plist
```

## Recommended Setup for Server

### Option A: System-Wide (Best for Dedicated Server)

```bash
# Set system-wide (requires admin)
sudo pmset -a sleep 0
sudo pmset -a disablesleep 1
sudo pmset -a disksleep 0

# Verify
pmset -g
```

**Pros:**
- ✅ Permanent (survives reboot)
- ✅ Works for all users
- ✅ No need to remember to run commands

**Cons:**
- ⚠️ Requires admin privileges
- ⚠️ Affects entire system

### Option B: Per-Session (Best for Shared Server)

```bash
# Start training
./scripts/run_training_server.sh

# Prevent sleep while training
./scripts/prevent_sleep.sh
```

**Pros:**
- ✅ No admin needed
- ✅ Only affects your session
- ✅ Stops automatically when training completes

**Cons:**
- ⚠️ Need to run each time
- ⚠️ Stops on reboot

### Option C: Hybrid (Recommended)

1. **Set display sleep** (doesn't affect training):
   ```bash
   # Display can sleep, but computer stays awake
   sudo pmset -a displaysleep 10
   ```

2. **Use caffeinate for training**:
   ```bash
   ./scripts/prevent_sleep.sh
   ```

## Complete Workflow

```bash
# 1. SSH into server
ssh user@mac-mini-ip
cd /path/to/ai-ml-trading-bot

# 2. Configure energy settings (one-time, optional)
./scripts/configure_energy_saver.sh
# Or manually: System Preferences → Energy Saver

# 3. Start training
./scripts/run_training_server.sh

# 4. Prevent sleep
./scripts/prevent_sleep.sh

# 5. Disconnect (everything continues)
exit
```

## Verify Settings

### Check Current Power Settings
```bash
pmset -g
```

Look for:
- `sleep` should be `0` (never sleep)
- `disablesleep` should be `1` (prevent idle sleep)
- `disksleep` should be `0` (never sleep disks)

### Check if Caffeinate is Running
```bash
ps aux | grep caffeinate
```

### Test Sleep Prevention
```bash
# Start caffeinate
caffeinate -d

# Turn off display (close laptop lid or turn off monitor)
# Computer should stay awake

# Check system is still responsive
uptime
```

## Troubleshooting

### Mac Still Goes to Sleep

**Check:**
1. Is caffeinate running? `ps aux | grep caffeinate`
2. Are system settings correct? `pmset -g`
3. Is Energy Saver configured? System Preferences

**Solutions:**
```bash
# Force prevent sleep
sudo pmset -a sleep 0 disablesleep 1

# Use caffeinate
caffeinate -d
```

### Display Turns Off (This is OK!)

The display can sleep - this doesn't affect training. Only the computer needs to stay awake.

### Settings Reset After Reboot

**Solution**: Use system-wide settings:
```bash
sudo pmset -a sleep 0 disablesleep 1 disksleep 0
```

Or create a launchd service that runs on boot.

## Best Practices

1. **For dedicated server**: Use system-wide settings
2. **For shared server**: Use caffeinate per session
3. **Always verify**: Check `pmset -g` after changes
4. **Monitor**: Use `uptime` to verify system stays awake
5. **Test**: Turn off display and verify training continues

## Quick Reference

```bash
# Prevent sleep (temporary)
caffeinate -d

# Prevent sleep while process runs
caffeinate -w <PID>

# Prevent sleep (permanent, requires admin)
sudo pmset -a sleep 0

# Check settings
pmset -g

# Stop caffeinate
pkill caffeinate
```

Your Mac mini will now stay awake for training! 🚀



