"""
Rate limiting utilities for API requests.

Implements token bucket algorithm to prevent exceeding API rate limits.
"""

import time
import threading
from contextlib import contextmanager
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class TokenBucketLimiter:
    """Token bucket rate limiter.

    Implements the token bucket algorithm for smooth rate limiting
    with support for burst capacity.

    Attributes:
        tokens_per_second: Rate at which tokens are added
        bucket_size: Maximum number of tokens (burst capacity)
        tokens: Current number of available tokens
        last_update: Timestamp of last token update
    """

    def __init__(self, tokens_per_second: float = 2.0, bucket_size: int = 10):
        """Initialize token bucket rate limiter.

        Args:
            tokens_per_second: Rate limit (requests per second)
            bucket_size: Maximum burst size

        Example:
            >>> # Allow 2 requests/second with burst of 10
            >>> limiter = TokenBucketLimiter(tokens_per_second=2.0, bucket_size=10)
        """
        if tokens_per_second <= 0:
            raise ValueError("tokens_per_second must be positive")
        if bucket_size <= 0:
            raise ValueError("bucket_size must be positive")

        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = float(bucket_size)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time.

        Called internally before each token acquisition.
        """
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.bucket_size, self.tokens + elapsed * self.tokens_per_second
        )
        self.last_update = now

    def acquire(
        self, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None
    ) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait for tokens; if False, return immediately
            timeout: Maximum time to wait for tokens (None = wait forever)

        Returns:
            True if tokens acquired, False if not (only when blocking=False)

        Raises:
            ValueError: If tokens is not positive
            TimeoutError: If timeout exceeded while waiting

        Example:
            >>> limiter = TokenBucketLimiter()
            >>> if limiter.acquire():
            ...     # Make API request
            ...     fetch_data()
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        start_time = time.time()

        while True:
            with self._lock:
                self._refill_tokens()

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(
                        f"Acquired {tokens} token(s). "
                        f"Remaining: {self.tokens:.2f}/{self.bucket_size}"
                    )
                    return True

                # Non-blocking mode
                if not blocking:
                    logger.debug(
                        f"Failed to acquire {tokens} token(s) (non-blocking). "
                        f"Available: {self.tokens:.2f}"
                    )
                    return False

                # Check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        raise TimeoutError(
                            f"Failed to acquire {tokens} token(s) within {timeout}s"
                        )

                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.tokens_per_second

                # Limit wait time for timeout checking
                if timeout is not None:
                    remaining_time = timeout - (time.time() - start_time)
                    wait_time = min(wait_time, remaining_time)

            # Sleep outside the lock
            logger.debug(f"Waiting {wait_time:.2f}s for tokens to refill")
            time.sleep(wait_time)

    def wait_for_token(self) -> None:
        """Wait until at least one token is available.

        Convenience method equivalent to acquire(tokens=1, blocking=True).

        Example:
            >>> limiter = TokenBucketLimiter()
            >>> limiter.wait_for_token()
            >>> # Now safe to make API request
        """
        self.acquire(tokens=1, blocking=True)

    @contextmanager
    def throttle(self, tokens: int = 1):
        """Context manager for rate-limited operations.

        Automatically acquires tokens before entering the context
        and releases control when done.

        Args:
            tokens: Number of tokens to acquire

        Yields:
            None

        Example:
            >>> limiter = TokenBucketLimiter()
            >>> with limiter.throttle():
            ...     response = api.fetch_data()
        """
        self.acquire(tokens=tokens, blocking=True)
        try:
            yield
        finally:
            # No cleanup needed for token bucket
            pass

    def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of tokens currently in bucket

        Example:
            >>> limiter = TokenBucketLimiter()
            >>> print(f"Available tokens: {limiter.get_available_tokens()}")
        """
        with self._lock:
            self._refill_tokens()
            return self.tokens

    def reset(self) -> None:
        """Reset the bucket to full capacity.

        Example:
            >>> limiter = TokenBucketLimiter()
            >>> limiter.reset()  # Fill bucket completely
        """
        with self._lock:
            self.tokens = float(self.bucket_size)
            self.last_update = time.time()
            logger.debug("Rate limiter reset to full capacity")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TokenBucketLimiter("
            f"rate={self.tokens_per_second}/s, "
            f"burst={self.bucket_size}, "
            f"available={self.tokens:.2f})"
        )
