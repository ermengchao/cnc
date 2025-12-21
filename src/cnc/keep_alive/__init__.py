from enum import Enum
from typing import Callable, Optional

from . import polling, relogin


class KeepAliveMode(str, Enum):
    polling = "polling"
    relogin = "relogin"


def keep_alive(
    mode: KeepAliveMode,
    *,
    test_func: Optional[Callable[[], int]] = None,
    interval_seconds: int = 300,
    userId: str | None = None,
    password: str | None = None,
    service: str | None = None,
    portalUrl: str | None = None,
    at: str = "05:00",
) -> None:
    if mode == KeepAliveMode.polling:
        if test_func is None:
            raise ValueError("polling mode requires test_func")
        return polling.run(test_func=test_func, interval_seconds=interval_seconds)

    if mode == KeepAliveMode.relogin:
        missing = [
            k
            for k, v in {
                "userId": userId,
                "password": password,
                "service": service,
                "portalUrl": portalUrl,
            }.items()
            if not v
        ]
        if missing:
            raise ValueError(f"relogin mode missing: {', '.join(missing)}")
        return relogin.run(
            userId=userId,
            password=password,
            service=service,
            portalUrl=portalUrl,
            at=at,
        )

    raise ValueError(f"unknown mode: {mode}")
