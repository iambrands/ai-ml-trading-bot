"""Utility functions for datetime handling with timezone-aware/naive conversions."""

from datetime import datetime, timezone
from typing import Optional


def make_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert timezone-aware datetime to naive UTC datetime.
    
    PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns expect naive datetimes.
    This function ensures compatibility by converting timezone-aware datetimes
    to naive UTC datetimes (which is what they represent anyway).
    
    Args:
        dt: Datetime object (timezone-aware or naive)
        
    Returns:
        Naive datetime in UTC, or None if input is None
        
    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime.now(timezone.utc)
        >>> naive = make_naive_utc(dt)
        >>> assert naive.tzinfo is None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    # Already naive, return as-is
    return dt


def now_naive_utc() -> datetime:
    """
    Get current UTC time as naive datetime.
    
    Convenience function for getting current time in naive UTC format
    suitable for database TIMESTAMP WITHOUT TIME ZONE columns.
    
    Returns:
        Current UTC time as naive datetime
        
    Examples:
        >>> now = now_naive_utc()
        >>> assert now.tzinfo is None
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

