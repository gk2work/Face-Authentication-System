"""Retry mechanisms with exponential backoff for transient failures"""

import time
import asyncio
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import random

from app.core.logging import logger
from app.core.config import settings


class RetryExhaustedError(Exception):
    """Exception raised when all retry attempts are exhausted"""
    pass


class RetryStrategy:
    """Retry strategy with exponential backoff"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to prevent thundering herd
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential delay
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter (random factor between 0.5 and 1.5)
        if self.jitter:
            jitter_factor = 0.5 + random.random()
            delay *= jitter_factor
        
        return delay
    
    def should_retry(
        self,
        attempt: int,
        exception: Exception,
        retryable_exceptions: Tuple[Type[Exception], ...]
    ) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            attempt: Current attempt number
            exception: Exception that occurred
            retryable_exceptions: Tuple of exception types to retry
            
        Returns:
            True if should retry, False otherwise
        """
        # Check if max attempts reached
        if attempt >= self.max_attempts:
            return False
        
        # Check if exception is retryable
        return isinstance(exception, retryable_exceptions)


def retry_with_backoff(
    max_attempts: int = None,
    initial_delay: float = None,
    max_delay: float = None,
    exponential_base: float = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum retry attempts (default from settings)
        initial_delay: Initial delay in seconds (default from settings)
        max_delay: Maximum delay in seconds (default from settings)
        exponential_base: Base for exponential backoff (default from settings)
        retryable_exceptions: Tuple of exception types to retry
        on_retry: Optional callback function called on each retry
    """
    # Use settings defaults if not provided
    max_attempts = max_attempts or settings.MAX_RETRY_ATTEMPTS
    initial_delay = initial_delay or settings.RETRY_INITIAL_DELAY
    max_delay = max_delay or settings.RETRY_MAX_DELAY
    exponential_base = exponential_base or settings.RETRY_EXPONENTIAL_BASE
    
    strategy = RetryStrategy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if not strategy.should_retry(attempt, e, retryable_exceptions):
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {attempt + 1} attempts: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    delay = strategy.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s delay. Error: {str(e)}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            raise RetryExhaustedError(
                f"Failed after {max_attempts} attempts: {str(last_exception)}"
            ) from last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if not strategy.should_retry(attempt, e, retryable_exceptions):
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {attempt + 1} attempts: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    delay = strategy.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s delay. Error: {str(e)}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    # Wait before retrying
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            raise RetryExhaustedError(
                f"Failed after {max_attempts} attempts: {str(last_exception)}"
            ) from last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class DeadLetterQueue:
    """Dead letter queue for failed items after max retries"""
    
    def __init__(self):
        self._queue = []
        self._max_size = 10000
    
    def add(
        self,
        item: Any,
        error: Exception,
        attempts: int,
        metadata: Optional[dict] = None
    ):
        """
        Add failed item to dead letter queue
        
        Args:
            item: Failed item data
            error: Exception that caused failure
            attempts: Number of attempts made
            metadata: Optional metadata
        """
        if len(self._queue) >= self._max_size:
            logger.warning("Dead letter queue is full, removing oldest item")
            self._queue.pop(0)
        
        entry = {
            "item": item,
            "error": str(error),
            "error_type": type(error).__name__,
            "attempts": attempts,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        self._queue.append(entry)
        
        logger.error(
            f"Item added to dead letter queue after {attempts} attempts: "
            f"{entry['error_type']}: {str(error)}"
        )
    
    def get_all(self) -> list:
        """Get all items in dead letter queue"""
        return self._queue.copy()
    
    def get_count(self) -> int:
        """Get number of items in dead letter queue"""
        return len(self._queue)
    
    def clear(self):
        """Clear all items from dead letter queue"""
        count = len(self._queue)
        self._queue.clear()
        logger.info(f"Cleared {count} items from dead letter queue")
    
    def remove(self, index: int) -> Optional[dict]:
        """Remove and return item at index"""
        if 0 <= index < len(self._queue):
            return self._queue.pop(index)
        return None
    
    def get_statistics(self) -> dict:
        """Get dead letter queue statistics"""
        if not self._queue:
            return {
                "count": 0,
                "error_types": {},
                "oldest_timestamp": None,
                "newest_timestamp": None
            }
        
        error_types = {}
        for entry in self._queue:
            error_type = entry["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        timestamps = [entry["timestamp"] for entry in self._queue]
        
        return {
            "count": len(self._queue),
            "error_types": error_types,
            "oldest_timestamp": min(timestamps),
            "newest_timestamp": max(timestamps)
        }


# Global dead letter queue instance
dead_letter_queue = DeadLetterQueue()
