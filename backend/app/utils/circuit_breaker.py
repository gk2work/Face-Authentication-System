"""Circuit breaker pattern implementation for external service calls"""

import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from app.core.logging import logger


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            success_threshold: Successful calls needed in half-open to close
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()
        
        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"timeout={timeout_seconds}s"
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_seconds
    
    def _record_success(self):
        """Record successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.success_threshold:
                self._close_circuit()
    
    def _record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit (reject requests)"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()
        logger.warning(
            f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures"
        )
    
    def _close_circuit(self):
        """Close the circuit (normal operation)"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.name}' CLOSED")
    
    def _half_open_circuit(self):
        """Half-open the circuit (testing recovery)"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN (testing recovery)")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN and self._should_attempt_reset():
            self._half_open_circuit()
        
        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Retry after {self.timeout_seconds}s."
            )
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            self._record_success()
            return result
            
        except self.expected_exception as e:
            self._record_failure()
            logger.error(
                f"Circuit breaker '{self.name}' recorded failure: {str(e)}"
            )
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN and self._should_attempt_reset():
            self._half_open_circuit()
        
        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Retry after {self.timeout_seconds}s."
            )
        
        try:
            # Execute async function
            result = await func(*args, **kwargs)
            self._record_success()
            return result
            
        except self.expected_exception as e:
            self._record_failure()
            logger.error(
                f"Circuit breaker '{self.name}' recorded failure: {str(e)}"
            )
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "failure_threshold": self.failure_threshold,
            "timeout_seconds": self.timeout_seconds
        }


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
    success_threshold: int = 2,
    expected_exception: type = Exception,
    fallback: Optional[Callable] = None
):
    """
    Decorator for applying circuit breaker pattern to functions
    
    Args:
        name: Circuit breaker identifier
        failure_threshold: Failures before opening circuit
        timeout_seconds: Seconds before attempting recovery
        success_threshold: Successes needed to close circuit
        expected_exception: Exception type to catch
        fallback: Optional fallback function to call when circuit is open
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
        success_threshold=success_threshold,
        expected_exception=expected_exception
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await breaker.call_async(func, *args, **kwargs)
            except CircuitBreakerError as e:
                if fallback:
                    logger.info(f"Circuit breaker open, using fallback for '{name}'")
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                if fallback:
                    logger.info(f"Circuit breaker open, using fallback for '{name}'")
                    return fallback(*args, **kwargs)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def register(self, breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self._breakers[breaker.name] = breaker
        logger.info(f"Registered circuit breaker: {breaker.name}")
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._breakers.get(name)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all registered circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers to closed state"""
        for breaker in self._breakers.values():
            breaker._close_circuit()
        logger.info("All circuit breakers reset")


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()
