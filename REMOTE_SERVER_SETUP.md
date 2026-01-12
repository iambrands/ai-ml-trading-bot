# Remote Server Training Setup

## Overview

This guide helps you run training on your Mac mini server that continues even when your MBP is closed or disconnected.

## Quick Start

### 1. Start Training on Server

```bash
# SSH into your Mac mini
ssh user@mac-mini-ip

# Navigate to project
cd /path/to/ai-ml-trading-bot

# Start training (will continue after disconnect)
./scripts/run_training_server.sh
```

### 2. Disconnect Safely

The training will continue running. You can:
- Close your MBP
- Disconnect from SSH
- Close terminal

Training continues in the background!

### 3. Check Status Later

```bash
# SSH back in
ssh user@mac-mini-ip

# Check status
./scripts/check_training_status.sh

# View logs
tail -f logs/training_*.log
```

## Methods for Persistent Training

### Method 1: nohup (Recommended - Already Set Up)

The `run_training_server.sh` script uses `nohup` which:
- ✅ Runs process in background
- ✅ Survives SSH disconnection
- ✅ Logs to file
- ✅ Easy to monitor

**Usage:**
```bash
./scripts/run_training_server.sh [start-date] [end-date] [time-points]
```

**Example:**
```bash
./scripts/run_training_server.sh 2022-01-09T00:00:00Z 2026-01-08T23:59:59Z "1 3 7 14"
```

### Method 2: screen (Alternative)

If you prefer `screen`:

```bash
# Install screen (if not installed)
brew install screen

# Start screen session
screen -S training

# Run training
python scripts/train_models.py --start-date 2022-01-09T00:00:00Z --end-date 2026-01-08T23:59:59Z --time-points 1 3 7 14

# Detach: Press Ctrl+A then D
# Reattach: screen -r training
```

### Method 3: tmux (Alternative)

If you prefer `tmux`:

```bash
# Install tmux (if not installed)
brew install tmux

# Start tmux session
tmux new -s training

# Run training
python scripts/train_models.py --start-date 2022-01-09T00:00:00Z --end-date 2026-01-08T23:59:59Z --time-points 1 3 7 14

# Detach: Press Ctrl+B then D
# Reattach: tmux attach -t training
```

### Method 4: launchd Service (macOS Native)

For automatic startup and management:

```bash
# Create launchd plist (see below)
# Install service
launchctl load ~/Library/LaunchAgents/com.polymarket.training.plist

# Start service
launchctl start com.polymarket.training

# Check status
launchctl list | grep training

# View logs
tail -f ~/Library/Logs/polymarket-training.log
```

## Monitoring Training

### Check Status

```bash
# Quick status check
./scripts/check_training_status.sh

# Or manually
ps aux | grep train_models
ls -lh data/models/
```

### View Logs

```bash
# Latest log
tail -f logs/training_*.log

# All logs
ls -lht logs/

# Search for errors
grep -i error logs/training_*.log
```

### Monitor Progress

```bash
# Run monitor script (in separate terminal)
python scripts/monitor_training.py --interval 60
```

## Stopping Training

### If Using nohup Script

```bash
# Check PID
cat .training.pid

# Stop training
kill $(cat .training.pid)

# Or force stop
kill -9 $(cat .training.pid)
```

### If Using screen/tmux

```bash
# Reattach and press Ctrl+C
screen -r training
# or
tmux attach -t training
```

## Ensuring Server Stays Awake

### Prevent Sleep on Mac mini

```bash
# Prevent sleep (until reboot)
caffeinate -d

# Or prevent sleep for specific time (e.g., 8 hours)
caffeinate -d -t 28800

# Or prevent sleep while specific process runs
caffeinate -w $(cat .training.pid)
```

### System Settings

1. System Preferences → Energy Saver
2. Uncheck "Put hard disks to sleep when possible"
3. Set "Computer sleep" to "Never" (or long duration)
4. Set "Display sleep" to desired time (doesn't affect training)

## SSH Configuration

### Keep SSH Connection Alive

Add to `~/.ssh/config` on your MBP:

```
Host mac-mini
    HostName your-mac-mini-ip
    User your-username
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Auto-Reconnect Script

```bash
#!/bin/bash
# auto_reconnect.sh
while true; do
    ssh user@mac-mini-ip "./scripts/check_training_status.sh"
    sleep 300  # Check every 5 minutes
done
```

## Production Training Command

Based on your data check (579 markets available):

```bash
./scripts/run_training_server.sh \
    2022-01-09T00:00:00Z \
    2026-01-08T23:59:59Z \
    "1 3 7 14"
```

This will:
- Use 579 markets
- Generate ~2,316 training examples (579 × 4 time points)
- Run in background
- Survive disconnection
- Log everything

## Troubleshooting

### Training Stops After Disconnect

**Solution**: Make sure you're using `nohup`, `screen`, or `tmux`

### Can't Find Process

```bash
# Check all Python processes
ps aux | grep python

# Check for training specifically
ps aux | grep train_models
```

### Logs Not Updating

```bash
# Check if process is running
ps -p $(cat .training.pid)

# Check log file permissions
ls -l logs/

# Check disk space
df -h
```

### Server Goes to Sleep

**Solution**: Use `caffeinate` or adjust Energy Saver settings

## Best Practices

1. **Always use the script**: `./scripts/run_training_server.sh`
2. **Check status before starting**: `./scripts/check_training_status.sh`
3. **Monitor logs**: `tail -f logs/training_*.log`
4. **Keep server awake**: Use `caffeinate` or Energy Saver settings
5. **Set up monitoring**: Run `monitor_training.py` in separate session

## Complete Workflow

```bash
# 1. SSH into server
ssh user@mac-mini-ip
cd /path/to/ai-ml-trading-bot

# 2. Check current status
./scripts/check_training_status.sh

# 3. Start training (if not running)
./scripts/run_training_server.sh

# 4. Disconnect (training continues)
exit

# 5. Later: Check status
ssh user@mac-mini-ip
cd /path/to/ai-ml-trading-bot
./scripts/check_training_status.sh
tail -f logs/training_*.log
```

Your training will now run independently on the server! 🚀



