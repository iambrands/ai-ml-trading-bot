"""Retry utilities for async operations."""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union

from ..utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Any],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each failure
        exceptions: Exception types to catch and retry on

    Returns:
        Function result

    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    "Retry attempt failed",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(e),
                    next_delay=current_delay,
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    "All retry attempts failed",
                    max_attempts=max_attempts,
                    error=str(e),
                )

    if last_exception:
        raise last_exception

    raise RuntimeError("Unexpected retry failure")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each failure
        exceptions: Exception types to catch and retry on
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async def _func() -> Any:
                return await func(*args, **kwargs)

            return await retry_async(_func, max_attempts, delay, backoff, exceptions)

        return wrapper

    return decorator



