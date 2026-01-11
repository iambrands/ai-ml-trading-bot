#!/usr/bin/env python3
"""Monitor training progress and alert when models are ready."""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_training_complete():
    """Check if training has completed by looking for model files."""
    models_dir = Path("data/models")
    
    required_files = [
        "xgboost_model.pkl",
        "lightgbm_model.pkl",
    ]
    
    all_present = all((models_dir / f).exists() for f in required_files)
    
    if all_present:
        # Check file modification times
        files = [models_dir / f for f in required_files]
        mod_times = [f.stat().st_mtime for f in files]
        latest_time = max(mod_times)
        
        return True, latest_time
    
    return False, None

def send_alert():
    """Send alert that training is complete."""
    print("\n" + "="*60)
    print("🎉 MODEL TRAINING COMPLETE! 🎉")
    print("="*60)
    print("\n✅ Models have been successfully trained!")
    print("\n📁 Model files created:")
    
    models_dir = Path("data/models")
    for file in models_dir.glob("*.pkl"):
        size = file.stat().st_size / (1024 * 1024)  # MB
        mod_time = datetime.fromtimestamp(file.stat().st_mtime)
        print(f"   - {file.name} ({size:.2f} MB, updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    if (models_dir / "ensemble_config.json").exists():
        print(f"   - ensemble_config.json")
    
    print("\n🚀 Next Steps:")
    print("   1. Restart your API server:")
    print("      uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload")
    print("\n   2. Open the UI:")
    print("      http://localhost:8001/")
    print("\n   3. Go to Predictions tab to see model predictions!")
    print("\n   4. Check Signals tab for trading opportunities!")
    print("\n" + "="*60 + "\n")
    
    # Try to play a system sound (macOS)
    if sys.platform == "darwin":
        os.system("afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || echo '🔔 Training complete!'")
    elif sys.platform == "linux":
        os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || echo '🔔 Training complete!'")
    else:
        print("🔔 Training complete!")

def monitor_training(check_interval=30):
    """Monitor training progress."""
    print("🔍 Monitoring training progress...")
    print(f"   Checking every {check_interval} seconds")
    print("   Press Ctrl+C to stop monitoring\n")
    
    last_check = None
    start_time = time.time()
    
    try:
        while True:
            complete, mod_time = check_training_complete()
            
            if complete:
                # Only alert if files were just created (within last check interval)
                if last_check is None or (mod_time and mod_time > last_check):
                    elapsed = time.time() - start_time
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    print(f"\n⏱️  Training completed in {minutes}m {seconds}s")
                    send_alert()
                    return True
                else:
                    # Models already exist, just waiting
                    print(f"⏳ Models exist, waiting for updates... ({datetime.now().strftime('%H:%M:%S')})")
            else:
                elapsed = time.time() - start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                print(f"⏳ Waiting for models... ({minutes}m {seconds}s elapsed)", end="\r")
            
            last_check = mod_time if mod_time else time.time()
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor model training progress")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)",
    )
    
    args = parser.parse_args()
    
    # Check if training is already complete
    complete, _ = check_training_complete()
    if complete:
        print("✅ Models already exist!")
        send_alert()
    else:
        monitor_training(check_interval=args.interval)


