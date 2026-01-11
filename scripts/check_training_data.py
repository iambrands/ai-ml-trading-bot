#!/usr/bin/env python3
"""Check available training data across different date ranges."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.sources.polymarket import PolymarketDataSource


async def check_available_data():
    """Check how many resolved markets are available in different date ranges."""
    print("🔍 Checking available training data...\n")
    
    async with PolymarketDataSource() as pm:
        end_date = datetime.now(timezone.utc)
        
        ranges = [
            (90, "Last 90 days"),
            (180, "Last 6 months"),
            (365, "Last 1 year"),
            (730, "Last 2 years"),
            (1095, "Last 3 years"),
            (1460, "Last 4 years"),
            (1825, "Last 5 years"),
        ]
        
        results = []
        
        for days, label in ranges:
            start_date = end_date - timedelta(days=days)
            print(f"Checking {label}...", end=" ", flush=True)
            
            try:
                markets = await pm.fetch_resolved_markets(start_date, end_date, limit=10000)
                
                yes_count = sum(1 for m in markets if m.outcome == "YES")
                no_count = sum(1 for m in markets if m.outcome == "NO")
                
                results.append({
                    "label": label,
                    "days": days,
                    "count": len(markets),
                    "yes": yes_count,
                    "no": no_count,
                    "start_date": start_date,
                })
                
                status = "✅" if len(markets) >= 500 else "⚠️" if len(markets) >= 100 else "❌"
                print(f"{status} {len(markets)} markets (YES: {yes_count}, NO: {no_count})")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    "label": label,
                    "days": days,
                    "count": 0,
                    "error": str(e),
                })
        
        print("\n" + "="*60)
        print("📊 Summary")
        print("="*60)
        
        # Find best range
        best = max(results, key=lambda x: x.get("count", 0))
        
        if best["count"] >= 500:
            print(f"\n✅ Production Ready: {best['label']} has {best['count']} markets")
            print(f"   Start date: {best['start_date'].date()}")
            print(f"   End date: {end_date.date()}")
            print(f"\n🚀 Recommended training command:")
            print(f"   python scripts/train_models.py \\")
            print(f"       --start-date {best['start_date'].isoformat()} \\")
            print(f"       --end-date {end_date.isoformat()} \\")
            print(f"       --time-points 1 3 7 14")
        elif best["count"] >= 100:
            print(f"\n⚠️  Limited Data: {best['label']} has {best['count']} markets")
            print(f"   Consider using multiple time points to increase examples")
            print(f"   Or wait for more markets to resolve")
        else:
            print(f"\n❌ Insufficient Data: Maximum {best['count']} markets found")
            print(f"   Consider:")
            print(f"   - Using alternative data sources")
            print(f"   - Manual data collection")
            print(f"   - Data augmentation techniques")
        
        print("\n" + "="*60)
        print("📈 Training Examples Estimate")
        print("="*60)
        
        for result in results:
            if result.get("count", 0) > 0:
                # Estimate with 5 time points
                examples_5 = result["count"] * 5
                # Estimate with 3 time points
                examples_3 = result["count"] * 3
                
                print(f"\n{result['label']}:")
                print(f"  Markets: {result['count']}")
                print(f"  Examples (3 time points): ~{examples_3}")
                print(f"  Examples (5 time points): ~{examples_5}")
                
                if examples_5 >= 2500:
                    print(f"  Status: ✅ Production ready")
                elif examples_5 >= 500:
                    print(f"  Status: ⚠️  Minimum for production")
                else:
                    print(f"  Status: ❌ Insufficient for production")


if __name__ == "__main__":
    asyncio.run(check_available_data())


