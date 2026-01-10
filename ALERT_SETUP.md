# Training Alert Setup

## Quick Start

Run the monitoring script to get alerted when training completes:

```bash
python scripts/monitor_training.py
```

This will:
- ✅ Check every 30 seconds for completed models
- 🔔 Alert you when training finishes
- 📊 Show model file details
- 🚀 Provide next steps

## Usage Options

### Basic Monitoring (30 second checks)
```bash
python scripts/monitor_training.py
```

### Custom Check Interval (e.g., every 10 seconds)
```bash
python scripts/monitor_training.py --interval 10
```

### Check if Already Complete
```bash
python scripts/monitor_training.py
# If models exist, it will immediately alert you
```

## What the Alert Shows

When training completes, you'll see:

```
🎉 MODEL TRAINING COMPLETE! 🎉

📁 Model files created:
   - xgboost_model.pkl (2.5 MB, updated: 2026-01-08 14:30:15)
   - lightgbm_model.pkl (1.8 MB, updated: 2026-01-08 14:30:20)
   - ensemble_config.json

🚀 Next Steps:
   1. Restart your API server
   2. Open the UI
   3. Go to Predictions tab
   4. Check Signals tab
```

## Background Monitoring

Run in background and get notified:

```bash
# Start monitoring in background
nohup python scripts/monitor_training.py > training_monitor.log 2>&1 &

# Check status
tail -f training_monitor.log

# Stop monitoring
pkill -f monitor_training.py
```

## Alternative: Manual Check

If you prefer to check manually:

```bash
# Check if models exist
ls -lh data/models/

# Check training process
ps aux | grep train_models

# View training logs
tail -f training_output.log
```

## System Notifications

The script will try to play a system sound when training completes:
- **macOS**: Plays system sound
- **Linux**: Plays notification sound (if available)
- **Windows**: Prints alert message

## Integration with Training

You can also run training and monitoring together:

```bash
# Terminal 1: Start training
python scripts/train_models.py --start-date 2024-01-01T00:00:00Z --end-date 2026-01-08T23:59:59Z --time-points 1 7

# Terminal 2: Monitor progress
python scripts/monitor_training.py
```

The monitor will automatically detect when models are created! 🎯

