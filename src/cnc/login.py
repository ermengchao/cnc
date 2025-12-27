from __future__ import annotations

import requests

from cnc.portal import get_portal_info
# from cnc.probe import NetworkState, detect_network_status


class LoginError(Exception):
    """Raised when portal login fails."""

    pass


def do_login(
    user_id: str,
    password: str,
    service: str,
    *,
    portal_url: str | None = None,
    query_string: str | None = None,
    timeout: float = 2.0,
    verify_tls: bool = False,
) -> None:
    """Perform a portal login request.

    Args:
        user_id: User identifier for the portal.
        password: User password.
        service: Service name to authenticate against.
        portal_url: Optional portal base URL. If absent, it is discovered.
        query_string: Optional auth query string. If absent, it is discovered.
        timeout: Request timeout in seconds.
        verify_tls: Whether to verify TLS certificates.

    Returns:
        None.
    """
    if not portal_url or not query_string:
        info = get_portal_info(timeout=timeout, verify_tls=verify_tls)
        portal_url = info.portal_url
        query_string = info.query_string

    url = f"{portal_url}/eportal/InterFace.do?method=login"

    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    payload = {
        "userId": user_id,
        "password": password,
        "service": service,
        "queryString": query_string,
        "operatorPwd": "",
        "operatorUserId": "",
        "validcode": "",
        "passwordEncrypt": "false",
    }

    try:
        response = requests.post(
            url=url,
            headers=headers,
            data=payload,
            timeout=timeout,
            verify=verify_tls,
            proxies={"http": None, "https": None},
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        resp_json = response.json()
    except Exception as e:
        raise LoginError(f"request/json decode failed: {e}") from e

    result = resp_json.get("result")
    message = resp_json.get("message", "")

    if result == "success":
        return None
    elif result == "fail":
        raise LoginError(message or "login failed")
    else:
        raise LoginError(f"unknown response: {resp_json}")
