from __future__ import annotations

import time

class KeepAliveError(Exception):
    """Raised when keep-alive loop cannot continue."""


def run(test_func, interval_seconds: int = 300) -> None:
    """Run a polling loop to keep the connection alive.

    Args:
        test_func: Callable returning a status code.
        interval_seconds: Sleep interval between polls.

    Returns:
        None.
    """
    while True:
        result = test_func()
        if result == 1:
            time.sleep(interval_seconds)
            continue
        raise KeepAliveError("keep_logged_in_v1: offline or unexpected network status")
