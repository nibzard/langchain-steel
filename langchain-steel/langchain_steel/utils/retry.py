"""Retry logic and resilience patterns for Steel operations."""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

from tenacity import (
    AsyncRetrying,
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

from langchain_steel.utils.errors import (
    SteelAPIError,
    SteelError,
    SteelRateLimitError,
    SteelSessionError,
    SteelTimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SteelRetry:
    """Retry configuration and utilities for Steel operations."""
    
    # Default retry configuration
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_WAIT_MIN = 1
    DEFAULT_WAIT_MAX = 60
    DEFAULT_MULTIPLIER = 2
    
    # Retryable exceptions
    RETRYABLE_EXCEPTIONS = (
        SteelTimeoutError,
        SteelRateLimitError,
        SteelSessionError,
    )
    
    # API errors that should be retried (5xx server errors)
    RETRYABLE_API_ERRORS = (500, 502, 503, 504, 520, 521, 522, 523, 524)
    
    @classmethod
    def should_retry_api_error(cls, error: SteelAPIError) -> bool:
        """Determine if an API error should be retried.
        
        Args:
            error: Steel API error
            
        Returns:
            True if the error should be retried
        """
        if isinstance(error, SteelRateLimitError):
            return True
        
        if error.status_code in cls.RETRYABLE_API_ERRORS:
            return True
        
        return False
    
    @classmethod
    def should_retry_exception(cls, exception: Exception) -> bool:
        """Determine if an exception should be retried.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if the exception should be retried
        """
        if isinstance(exception, cls.RETRYABLE_EXCEPTIONS):
            return True
        
        if isinstance(exception, SteelAPIError):
            return cls.should_retry_api_error(exception)
        
        return False
    
    @classmethod
    def create_retrying(
        cls,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        wait_min: float = DEFAULT_WAIT_MIN,
        wait_max: float = DEFAULT_WAIT_MAX,
        multiplier: float = DEFAULT_MULTIPLIER,
        jitter: bool = True,
        reraise: bool = True,
    ) -> Retrying:
        """Create a tenacity Retrying instance with Steel defaults.
        
        Args:
            max_attempts: Maximum number of retry attempts
            wait_min: Minimum wait time in seconds
            wait_max: Maximum wait time in seconds
            multiplier: Exponential backoff multiplier
            jitter: Whether to add random jitter to wait times
            reraise: Whether to reraise the last exception
            
        Returns:
            Configured Retrying instance
        """
        if jitter:
            wait_strategy = wait_random_exponential(
                min=wait_min, max=wait_max, multiplier=multiplier
            )
        else:
            wait_strategy = wait_exponential(
                min=wait_min, max=wait_max, multiplier=multiplier
            )
        
        return Retrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=(
                retry_if_exception_type(cls.RETRYABLE_EXCEPTIONS) | 
                retry_if_exception(cls.should_retry_exception)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=reraise,
        )
    
    @classmethod
    def create_async_retrying(
        cls,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        wait_min: float = DEFAULT_WAIT_MIN,
        wait_max: float = DEFAULT_WAIT_MAX,
        multiplier: float = DEFAULT_MULTIPLIER,
        jitter: bool = True,
        reraise: bool = True,
    ) -> AsyncRetrying:
        """Create a tenacity AsyncRetrying instance with Steel defaults.
        
        Args:
            max_attempts: Maximum number of retry attempts
            wait_min: Minimum wait time in seconds
            wait_max: Maximum wait time in seconds
            multiplier: Exponential backoff multiplier
            jitter: Whether to add random jitter to wait times
            reraise: Whether to reraise the last exception
            
        Returns:
            Configured AsyncRetrying instance
        """
        if jitter:
            wait_strategy = wait_random_exponential(
                min=wait_min, max=wait_max, multiplier=multiplier
            )
        else:
            wait_strategy = wait_exponential(
                min=wait_min, max=wait_max, multiplier=multiplier
            )
        
        return AsyncRetrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=(
                retry_if_exception_type(cls.RETRYABLE_EXCEPTIONS) |
                retry_if_exception(cls.should_retry_exception)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=reraise,
        )


def retry_on_steel_error(
    max_attempts: int = SteelRetry.DEFAULT_MAX_ATTEMPTS,
    wait_min: float = SteelRetry.DEFAULT_WAIT_MIN,
    wait_max: float = SteelRetry.DEFAULT_WAIT_MAX,
    multiplier: float = SteelRetry.DEFAULT_MULTIPLIER,
    jitter: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry function on Steel errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time in seconds
        wait_max: Maximum wait time in seconds
        multiplier: Exponential backoff multiplier
        jitter: Whether to add random jitter to wait times
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retrying = SteelRetry.create_retrying(
            max_attempts=max_attempts,
            wait_min=wait_min,
            wait_max=wait_max,
            multiplier=multiplier,
            jitter=jitter,
        )
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retrying(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


def async_retry_on_steel_error(
    max_attempts: int = SteelRetry.DEFAULT_MAX_ATTEMPTS,
    wait_min: float = SteelRetry.DEFAULT_WAIT_MIN,
    wait_max: float = SteelRetry.DEFAULT_WAIT_MAX,
    multiplier: float = SteelRetry.DEFAULT_MULTIPLIER,
    jitter: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to retry async function on Steel errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time in seconds
        wait_max: Maximum wait time in seconds
        multiplier: Exponential backoff multiplier
        jitter: Whether to add random jitter to wait times
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        retrying = SteelRetry.create_async_retrying(
            max_attempts=max_attempts,
            wait_min=wait_min,
            wait_max=wait_max,
            multiplier=multiplier,
            jitter=jitter,
        )
        
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async for attempt in retrying:
                with attempt:
                    return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for Steel operations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = SteelError,
    ) -> None:
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            expected_exception: Exception type to track for failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.state != "open":
            return False
        
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            SteelError: If circuit is open
            Exception: Original exception from function
        """
        if self.state == "open" and not self._should_attempt_reset():
            raise SteelError(
                f"Circuit breaker is open. Will retry after {self.recovery_timeout}s.",
                details={
                    "failure_count": self.failure_count,
                    "last_failure_time": self.last_failure_time,
                    "state": self.state,
                }
            )
        
        # If we're in half-open state or attempting reset
        if self.state == "open":
            self.state = "half-open"
        
        try:
            result = func(*args, **kwargs)
            # Success - reset failure count and close circuit
            self.failure_count = 0
            self.state = "closed"
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s."
                )
            else:
                self.state = "closed"
            
            raise e
    
    async def async_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call async function through circuit breaker.
        
        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            SteelError: If circuit is open
            Exception: Original exception from function
        """
        if self.state == "open" and not self._should_attempt_reset():
            raise SteelError(
                f"Circuit breaker is open. Will retry after {self.recovery_timeout}s.",
                details={
                    "failure_count": self.failure_count,
                    "last_failure_time": self.last_failure_time,
                    "state": self.state,
                }
            )
        
        # If we're in half-open state or attempting reset
        if self.state == "open":
            self.state = "half-open"
        
        try:
            result = await func(*args, **kwargs)
            # Success - reset failure count and close circuit
            self.failure_count = 0
            self.state = "closed"
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s."
                )
            else:
                self.state = "closed"
            
            raise e


def with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to wrap function with circuit breaker.
    
    Args:
        circuit_breaker: Circuit breaker instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return circuit_breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


def with_async_circuit_breaker(
    circuit_breaker: CircuitBreaker,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to wrap async function with circuit breaker.
    
    Args:
        circuit_breaker: Circuit breaker instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await circuit_breaker.async_call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator