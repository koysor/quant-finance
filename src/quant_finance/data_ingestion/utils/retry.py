"""
Retry logic with exponential backoff for handling transient failures.
"""

import time
import logging
from typing import Callable, Any, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class ExponentialBackoffRetry:
    """Retry strategy using exponential backoff.

    Retries failed operations with increasing delays between attempts,
    useful for handling transient network or server errors.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Multiplier for each retry
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry strategy.

        Args:
            max_retries: Maximum retry attempts (0 = no retries)
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation

        Example:
            >>> # Retry up to 3 times with delays of 1s, 2s, 4s
            >>> retry = ExponentialBackoffRetry(max_retries=3, base_delay=1.0)
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if exponential_base <= 1:
            raise ValueError("exponential_base must be greater than 1")

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised

        Returns:
            True if should retry, False otherwise

        Note:
            Network errors and server errors (5xx) are retried.
            Client errors (4xx except rate limits) are not retried.
        """
        from ..exceptions import (
            RateLimitError,
            SymbolNotFoundError,
            ValidationError,
            FetchError,
        )

        # Don't retry validation errors or symbol not found
        if isinstance(exception, (ValidationError, SymbolNotFoundError)):
            return False

        # Always retry rate limit errors (with backoff)
        if isinstance(exception, RateLimitError):
            return True

        # Retry fetch errors and network-related exceptions
        if isinstance(exception, FetchError):
            return True

        # Retry common network errors
        error_msg = str(exception).lower()
        retryable_errors = [
            "timeout",
            "connection",
            "network",
            "temporary",
            "unavailable",
            "500",
            "502",
            "503",
            "504",
        ]

        return any(err in error_msg for err in retryable_errors)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds for this attempt

        Example:
            >>> retry = ExponentialBackoffRetry(base_delay=1.0, exponential_base=2.0)
            >>> retry.calculate_delay(0)  # First retry
            1.0
            >>> retry.calculate_delay(1)  # Second retry
            2.0
            >>> retry.calculate_delay(2)  # Third retry
            4.0
        """
        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            The last exception if all retries fail

        Example:
            >>> retry = ExponentialBackoffRetry(max_retries=3)
            >>> result = retry.execute(api.fetch_data, symbol="AAPL")
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Log success after retries
                if attempt > 0:
                    logger.info(f"Succeeded after {attempt} retry(ies)")

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if attempt < self.max_retries and self.should_retry(e):
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    # Last attempt or non-retryable error
                    if attempt < self.max_retries:
                        logger.error(f"Non-retryable error: {e}")
                    else:
                        logger.error(
                            f"All {self.max_retries + 1} attempts failed. "
                            f"Last error: {e}"
                        )
                    raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception

    def __call__(self, func: Callable) -> Callable:
        """Decorator for retrying functions.

        Args:
            func: Function to decorate

        Returns:
            Decorated function with retry logic

        Example:
            >>> retry = ExponentialBackoffRetry(max_retries=3)
            >>>
            >>> @retry
            ... def fetch_data(symbol):
            ...     return api.get(symbol)
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)

        return wrapper

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExponentialBackoffRetry("
            f"max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}s, "
            f"max_delay={self.max_delay}s)"
        )


def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for retrying on specific exceptions.

    Simpler alternative to ExponentialBackoffRetry for quick use.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay between retries
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorator function

    Example:
        >>> @retry_on_exception(max_retries=3, base_delay=1.0)
        ... def fetch_stock_data(symbol):
        ...     return yf.download(symbol)
    """
    retry_strategy = ExponentialBackoffRetry(
        max_retries=max_retries, base_delay=base_delay
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator
