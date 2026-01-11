from enum import Enum
from . import polling, relogin


class KeepAliveMode(str, Enum):
    polling = "polling"
    relogin = "relogin"


def keep_alive(
    mode: KeepAliveMode,
    *,
    interval_seconds: int = 300,
    user_id: str | None = None,
    password: str | None = None,
    service: str | None = None,
    portal_url: str | None = None,
    run_at: str = "05:00",
) -> None:
    """
    Thin dispatcher: choose polling or relogin strategy.
    """

    if mode == KeepAliveMode.polling:
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
            raise ValueError(f"polling mode missing: {', '.join(missing)}")

        assert user_id is not None
        assert password is not None
        assert service is not None

        return polling.run(
            user_id=user_id,
            password=password,
            service=service,
            interval_seconds=interval_seconds,
            portal_url=portal_url,
        )

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

        assert user_id is not None
        assert password is not None
        assert service is not None

        return relogin.run(
            user_id=user_id,
            password=password,
            service=service,
            portal_url=portal_url,
            run_at=run_at,
        )

    raise ValueError(f"unknown mode: {mode}")
