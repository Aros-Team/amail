"""In-memory sliding window rate limiter."""

import time
from collections import deque
from threading import Lock


class SlidingWindowRateLimiter:
    """Per-key sliding window rate limiter using deques."""

    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = {}
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()

            window = self._windows[key]

            # Remove expired entries
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) < limit:
                window.append(now)
                return True
            return False

    def reset(self) -> None:
        """Clear all windows (for testing)."""
        with self._lock:
            self._windows.clear()


# Singleton instance
_rate_limiter = SlidingWindowRateLimiter()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Return the singleton rate limiter instance."""
    return _rate_limiter


def reset_rate_limits() -> None:
    """Reset all rate limit windows (for testing)."""
    _rate_limiter.reset()
