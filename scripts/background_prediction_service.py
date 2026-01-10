#!/usr/bin/env python3
"""Background service to continuously generate predictions."""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Configuration
# Auto-detect API base from environment or default to localhost
import os
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8002")
INTERVAL = 300  # 5 minutes in seconds
MAX_RETRIES = 3
RETRY_DELAY = 60  # 1 minute between retries


async def generate_predictions():
    """Call the prediction generation API endpoint."""
    import aiohttp
    
    url = f"{API_BASE}/predictions/generate"
    # Convert booleans to strings for query parameters
    params = {"auto_signals": "true", "auto_trades": "false", "limit": "50"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        "Predictions generated successfully",
                        status=data.get("status"),
                        message=data.get("message"),
                    )
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(
                        "API returned non-200 status",
                        status=response.status,
                        error=error_text[:200],
                    )
                    return False
    except asyncio.TimeoutError:
        logger.error("Request timed out after 5 minutes")
        return False
    except aiohttp.ClientError as e:
        logger.error("HTTP client error", error=str(e))
        return False
    except Exception as e:
        logger.error("Unexpected error calling API", error=str(e))
        return False


async def run_service():
    """Main service loop."""
    logger.info("Starting background prediction service")
    logger.info(f"API Base: {API_BASE}")
    logger.info(f"Update Interval: {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)")
    logger.info("Service will generate predictions automatically")
    
    consecutive_failures = 0
    
    while True:
        try:
            # Get current time in Central Time
            from zoneinfo import ZoneInfo
            ct_time = datetime.now(ZoneInfo("America/Chicago"))
            logger.info(f"Generating predictions at {ct_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            success = await generate_predictions()
            
            if success:
                consecutive_failures = 0
                logger.info(f"Next update in {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)")
            else:
                consecutive_failures += 1
                logger.warning(
                    f"Prediction generation failed (consecutive failures: {consecutive_failures})"
                )
                
                if consecutive_failures >= MAX_RETRIES:
                    logger.error(
                        f"Too many consecutive failures ({consecutive_failures}). "
                        f"Waiting {RETRY_DELAY} seconds before retry..."
                    )
                    await asyncio.sleep(RETRY_DELAY)
                    consecutive_failures = 0  # Reset after waiting
                else:
                    logger.info(f"Retrying in {INTERVAL} seconds...")
            
            # Wait for next interval
            await asyncio.sleep(INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
            break
        except Exception as e:
            logger.error("Unexpected error in service loop", error=str(e))
            await asyncio.sleep(INTERVAL)  # Wait before retrying


def main():
    """Entry point."""
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    main()

