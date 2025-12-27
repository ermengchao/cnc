from __future__ import annotations

import time
import schedule

from cnc.login import do_login, LoginError
from cnc.logout import do_logout, LogoutError


class KeepAliveError(Exception):
    """Raised when keep-alive loop cannot continue."""


def run(
    user_id: str,
    password: str,
    service: str,
    *,
    portal_url: str | None = None,
    run_at: str = "05:00",
    timeout: float = 2.0,
    verify_tls: bool = False,
) -> None:
    """Run a daily relogin schedule to refresh authentication.

    Args:
        user_id: User identifier for the portal.
        password: User password.
        service: Service name to authenticate against.
        portal_url: Optional portal base URL. If absent, it is discovered.
        run_at: Daily relogin time (HH:MM, 24h).
        timeout: Request timeout in seconds.
        verify_tls: Whether to verify TLS certificates.

    Returns:
        None.
    """
    def _do_logout_then_login():
        """Logout (best-effort) then login to refresh the session.

        Returns:
            None.
        """
        try:
            do_logout(
                portal_url=portal_url,
                timeout=timeout,
                verify_tls=verify_tls,
            )
        except LogoutError:
            pass

        try:
            do_login(
                user_id,
                password,
                service,
                portal_url=portal_url,
                timeout=timeout,
                verify_tls=verify_tls,
            )
        except LoginError:
            raise KeepAliveError("Failed to keep alive due to LoginError")

    schedule.clear()
    schedule.every().day.at(run_at).do(_do_logout_then_login)

    while True:
        schedule.run_pending()
        time.sleep(1)
