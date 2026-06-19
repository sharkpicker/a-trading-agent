# Copyright 2026 sharkpicker
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Rate limiting utilities for China A-share data sources.

Provides throttling decorators to prevent API rate-limiting and IP bans
when calling akshare and other data sources. Inspired by the rate-limiting
approach in TradingAgents-Astock (simonlin1212/TradingAgents-astock).

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from __future__ import annotations

import functools
import logging
import os
import random
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global rate limiter state (thread-safe)
# ---------------------------------------------------------------------------

# Minimum interval between akshare calls (seconds).
# Akshare wraps Eastmoney and other web APIs. Aggressive calling can trigger
# HTTP 429 or temporary IP bans. Default 0.8s provides ~1.25 req/s.
_AK_MIN_INTERVAL = float(os.environ.get("AK_MIN_INTERVAL", "0.8"))

# Minimum interval between mootdx calls (seconds).
# mootdx uses TCP 7709 to TDX servers. Rapid reconnection can cause drops.
_MOO_MIN_INTERVAL = float(os.environ.get("MOO_MIN_INTERVAL", "0.3"))

# Minimum interval between tencent HTTP calls (seconds).
_TENCENT_MIN_INTERVAL = float(os.environ.get("TENCENT_MIN_INTERVAL", "0.5"))

# Random jitter range (seconds) added to each wait to avoid thundering herd.
_JITTER_MIN = 0.05
_JITTER_MAX = 0.35

_lock = threading.Lock()
_last_call: dict[str, float] = {}


def _throttle(vendor: str, min_interval: float) -> None:
    """Block until at least ``min_interval`` seconds have passed since the
    last call to ``vendor``. A small random jitter is added to spread out
    concurrent requests across multiple threads/processes.
    """
    with _lock:
        last = _last_call.get(vendor, 0.0)
        now = time.time()
        elapsed = now - last
        wait = min_interval - elapsed
        if wait > 0:
            jitter = random.uniform(_JITTER_MIN, _JITTER_MAX)
            total_wait = wait + jitter
            logger.debug("Rate limit: sleeping %.2fs for %s", total_wait, vendor)
            time.sleep(total_wait)
        _last_call[vendor] = time.time()


def rate_limited(
    vendor: str = "akshare",
    min_interval: float | None = None,
) -> Callable:
    """Decorator that rate-limits a function to prevent API bans.

    Args:
        vendor: Vendor identifier used for per-vendor throttling.
        min_interval: Minimum seconds between calls. If None, uses the
            default for the vendor (akshare=0.8s, mootdx=0.3s, tencent=0.5s).

    Example:
        @rate_limited("akshare")
        def get_dragon_tiger_board(symbol: str) -> str:
            ...
    """
    if min_interval is None:
        defaults = {
            "akshare": _AK_MIN_INTERVAL,
            "mootdx": _MOO_MIN_INTERVAL,
            "tencent": _TENCENT_MIN_INTERVAL,
        }
        min_interval = defaults.get(vendor, 0.5)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _throttle(vendor, min_interval)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def rate_limited_retry(
    vendor: str = "akshare",
    min_interval: float | None = None,
    max_retries: int = 2,
    backoff_factor: float = 2.0,
) -> Callable:
    """Decorator that combines rate-limiting with exponential backoff retry.

    Useful for functions that occasionally hit transient rate limits or
    network errors from data sources.

    Args:
        vendor: Vendor identifier for throttling.
        min_interval: Minimum seconds between calls.
        max_retries: Maximum retry attempts on failure.
        backoff_factor: Multiplier for exponential backoff between retries.

    Example:
        @rate_limited_retry("akshare", max_retries=3)
        def get_northbound_flow(symbol: str) -> str:
            ...
    """
    if min_interval is None:
        defaults = {
            "akshare": _AK_MIN_INTERVAL,
            "mootdx": _MOO_MIN_INTERVAL,
            "tencent": _TENCENT_MIN_INTERVAL,
        }
        min_interval = defaults.get(vendor, 0.5)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _throttle(vendor, min_interval)
            last_error: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    # Only retry on rate-limit or transient network errors
                    if attempt < max_retries and any(
                        marker in error_str
                        for marker in [
                            "429",
                            "too many",
                            "rate limit",
                            "connection",
                            "timeout",
                            "temporarily",
                            "ban",
                            "封",
                            "频繁",
                        ]
                    ):
                        backoff = backoff_factor ** attempt + random.uniform(0.1, 0.5)
                        logger.warning(
                            "%s attempt %d/%d failed (%s), retrying in %.1fs",
                            fn.__name__, attempt + 1, max_retries + 1, e, backoff,
                        )
                        time.sleep(backoff)
                        _throttle(vendor, min_interval)
                    else:
                        raise
            # Should never reach here, but satisfy type checker
            raise last_error  # type: ignore[misc]
        return wrapper
    return decorator


__all__ = [
    "rate_limited",
    "rate_limited_retry",
]
