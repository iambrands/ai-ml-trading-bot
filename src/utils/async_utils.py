"""Async utility functions."""

import asyncio
from typing import Any, Callable, List, TypeVar

T = TypeVar("T")


async def gather_with_exceptions(*coros: Any, return_exceptions: bool = True) -> List[Any]:
    """
    Gather coroutines and handle exceptions gracefully.

    Args:
        *coros: Coroutines to gather
        return_exceptions: If True, exceptions are returned as results

    Returns:
        List of results (or exceptions if return_exceptions=True)
    """
    results = await asyncio.gather(*coros, return_exceptions=return_exceptions)
    return results


async def batch_process(
    items: List[T],
    processor: Callable[[T], Any],
    batch_size: int = 10,
    concurrency: int = 5,
) -> List[Any]:
    """
    Process items in batches with controlled concurrency.

    Args:
        items: Items to process
        processor: Async processor function
        batch_size: Number of items per batch
        concurrency: Maximum concurrent operations

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def process_with_semaphore(item: T) -> Any:
        async with semaphore:
            return await processor(item)

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batch_results = await asyncio.gather(*[process_with_semaphore(item) for item in batch])
        results.extend(batch_results)

    return results


async def timeout_wrapper(coro: Any, timeout: float) -> Any:
    """
    Execute coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds

    Returns:
        Coroutine result

    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    return await asyncio.wait_for(coro, timeout=timeout)

