from __future__ import annotations

import requests

from cnc.portal import get_portal_info


class LogoutError(Exception):
    """Raised when portal logout fails."""


def do_logout(
    *,
    portal_url: str | None = None,
    timeout: float = 2.0,
    verify_tls: bool = False,
) -> None:
    """Perform a portal logout request.

    Args:
        portal_url: Optional portal base URL. If absent, it is discovered.
        timeout: Request timeout in seconds.
        verify_tls: Whether to verify TLS certificates.

    Returns:
        None.
    """
    if not portal_url:
        info = get_portal_info(timeout=timeout, verify_tls=verify_tls)
        portal_url = info.portal_url

    if portal_url.startswith("http://") or portal_url.startswith("https://"):
        base = portal_url
    else:
        base = f"http://{portal_url}"

    url = f"{base}/eportal/InterFace.do?method=logout"

    try:
        response = requests.post(
            url,
            timeout=timeout,
            verify=verify_tls,
            proxies={"http": None, "https": None},
        )
    except Exception as e:
        raise LogoutError(f"request failed: {e}") from e

    if response.status_code != 200:
        raise LogoutError(f"unexpected status code: {response.status_code}")
