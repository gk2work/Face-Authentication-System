"""Resilience utilities combining circuit breaker and retry patterns"""

from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import asyncio

from app.core.logging import logger
from app.core.config import settings
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError, circuit_breaker_registry
from app.utils.retry import retry_with_backoff, RetryExhaustedError, dead_letter_queue
from app.utils.error_responses import ErrorCode, create_error_response


class ResilientService:
    """
    Base class for resilient services with circuit breaker and retry support
    
    Example usage:
        class MyService(ResilientService):
            def __init__(self):
                super().__init__(
                    service_name="my_service",
                    failure_threshold=5,
                    timeout_seconds=60
                )
            
            @retry_with_backoff(max_attempts=3)
            async def call_external_api(self, data):
                return await self.circuit_breaker.call_async(
                    self._make_api_call,
                    data
                )
            
            async def _make_api_call(self, data):
                # Actual API call implementation
                pass
    """
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = None,
        timeout_seconds: int = None,
        success_threshold: int = None
    ):
        """
        Initialize resilient service
        
        Args:
            service_name: Name of the service
            failure_threshold: Failures before opening circuit
            timeout_seconds: Seconds before attempting recovery
            success_threshold: Successes needed to close circuit
        """
        self.service_name = service_name
        
        # Create circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name=service_name,
            failure_threshold=failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            timeout_seconds=timeout_seconds or settings.CIRCUIT_BREAKER_TIMEOUT_SECONDS,
            success_threshold=success_threshold or settings.CIRCUIT_BREAKER_SUCCESS_THRESHOLD
        )
        
        # Register circuit breaker
        circuit_breaker_registry.register(self.circuit_breaker)
        
        logger.info(f"Resilient service '{service_name}' initialized")
    
    def get_health_status(self) -> dict:
        """Get health status of the service"""
        circuit_state = self.circuit_breaker.get_state()
        
        is_healthy = circuit_state["state"] == "closed"
        
        return {
            "service_name": self.service_name,
            "healthy": is_healthy,
            "circuit_breaker": circuit_state
        }


def resilient_call(
    service_name: str,
    max_retries: int = 3,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    fallback: Optional[Callable] = None
):
    """
    Decorator combining circuit breaker and retry patterns
    
    Args:
        service_name: Name of the service/operation
        max_retries: Maximum retry attempts
        failure_threshold: Failures before opening circuit
        timeout_seconds: Seconds before attempting recovery
        retryable_exceptions: Exceptions to retry
        fallback: Optional fallback function
    
    Example:
        @resilient_call(
            service_name="vector_search",
            max_retries=3,
            retryable_exceptions=(ConnectionError, TimeoutError)
        )
        async def search_vectors(query):
            # Implementation
            pass
    """
    # Create circuit breaker
    breaker = CircuitBreaker(
        name=service_name,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds
    )
    circuit_breaker_registry.register(breaker)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Call through circuit breaker
                    return await breaker.call_async(func, *args, **kwargs)
                    
                except CircuitBreakerError as e:
                    # Circuit is open, use fallback if available
                    if fallback:
                        logger.info(f"Circuit breaker open for '{service_name}', using fallback")
                        if asyncio.iscoroutinefunction(fallback):
                            return await fallback(*args, **kwargs)
                        return fallback(*args, **kwargs)
                    raise
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = settings.RETRY_INITIAL_DELAY * (settings.RETRY_EXPONENTIAL_BASE ** attempt)
                        delay = min(delay, settings.RETRY_MAX_DELAY)
                        
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} for '{service_name}' "
                            f"after {delay:.2f}s. Error: {str(e)}"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        # Max retries exhausted, add to dead letter queue
                        dead_letter_queue.add(
                            item={"function": func.__name__, "args": args, "kwargs": kwargs},
                            error=e,
                            attempts=max_retries,
                            metadata={"service_name": service_name}
                        )
                        
                        logger.error(
                            f"Max retries exhausted for '{service_name}' after {max_retries} attempts"
                        )
                        
                        raise RetryExhaustedError(
                            f"Failed after {max_retries} attempts: {str(e)}"
                        ) from e
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Call through circuit breaker
                    return breaker.call(func, *args, **kwargs)
                    
                except CircuitBreakerError as e:
                    # Circuit is open, use fallback if available
                    if fallback:
                        logger.info(f"Circuit breaker open for '{service_name}', using fallback")
                        return fallback(*args, **kwargs)
                    raise
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        import time
                        delay = settings.RETRY_INITIAL_DELAY * (settings.RETRY_EXPONENTIAL_BASE ** attempt)
                        delay = min(delay, settings.RETRY_MAX_DELAY)
                        
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} for '{service_name}' "
                            f"after {delay:.2f}s. Error: {str(e)}"
                        )
                        
                        time.sleep(delay)
                    else:
                        # Max retries exhausted, add to dead letter queue
                        dead_letter_queue.add(
                            item={"function": func.__name__, "args": args, "kwargs": kwargs},
                            error=e,
                            attempts=max_retries,
                            metadata={"service_name": service_name}
                        )
                        
                        logger.error(
                            f"Max retries exhausted for '{service_name}' after {max_retries} attempts"
                        )
                        
                        raise RetryExhaustedError(
                            f"Failed after {max_retries} attempts: {str(e)}"
                        ) from e
            
            raise last_exception
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_resilience_status() -> dict:
    """
    Get overall resilience status of all services
    
    Returns:
        Dictionary with circuit breaker states and dead letter queue stats
    """
    return {
        "circuit_breakers": circuit_breaker_registry.get_all_states(),
        "dead_letter_queue": dead_letter_queue.get_statistics()
    }
