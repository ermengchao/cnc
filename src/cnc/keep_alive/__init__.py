from enum import Enum
from typing import Callable, Optional

from . import polling, relogin
from cnc.client import CampusNetClient, StateError


class KeepAliveMode(str, Enum):
    polling = "polling"
    relogin = "relogin"


def _require_cache() -> None:
    """Ensure a cached portal_url exists before running keep-alive.

    Raises:
        StateError: If no cached portal_url is found.

    Returns:
        None.
    """
    client = CampusNetClient()
    cached = client.state.load()
    if not cached or not isinstance(cached.get("portal_url"), str):
        raise StateError(
            "No cached portal_url found. Please run `cnc login` once to "
            "initialize the cache before using other commands."
        )


def keep_alive(
    mode: KeepAliveMode,
    *,
    test_func: Optional[Callable[[], int]] = None,
    interval_seconds: int = 300,
    user_id: str | None = None,
    password: str | None = None,
    service: str | None = None,
    portal_url: str | None = None,
    run_at: str = "05:00",
) -> None:
    """Run keep-alive in polling or relogin mode.

    Args:
        mode: Keep-alive mode selector.
        test_func: Polling test function for polling mode.
        interval_seconds: Polling interval in seconds.
        user_id: User identifier for relogin mode.
        password: User password for relogin mode.
        service: Service name for relogin mode.
        portal_url: Optional portal base URL for relogin mode.
        run_at: Daily relogin time (HH:MM, 24h).

    Returns:
        None.
    """
    _require_cache()

    if mode == KeepAliveMode.polling:
        if test_func is None:
            raise ValueError("polling mode requires test_func")
        return polling.run(test_func=test_func, interval_seconds=interval_seconds)

    if mode == KeepAliveMode.relogin:
        missing = [
            k
            for k, v in {
                "user_id": user_id,
                "password": password,
                "service": service,
            }.items()
            if not v
        ]
        if missing:
            raise ValueError(f"relogin mode missing: {', '.join(missing)}")
        return relogin.run(
            user_id=user_id,
            password=password,
            service=service,
            portal_url=portal_url,
            run_at=run_at,
        )

    raise ValueError(f"unknown mode: {mode}")
