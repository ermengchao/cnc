from enum import Enum
import requests

from cnc.portal import get_portal_info


class NetworkState(str, Enum):
    ON_CAMPUS_UNAUTH = "on_campus_unauth"
    ON_CAMPUS_AUTH = "on_campus_auth"
    OFF_CAMPUS = "off_campus"
    UNKNOWN = "unknown"


def detect_network_status(
    redirect_url: str = "http://123.123.123.123/",
    timeout: float = 2.0,
    verify_tls: bool = False,
) -> NetworkState:
    """Detect current network/authentication state.

    Args:
        redirect_url: URL used to trigger captive portal redirection.
        timeout: Request timeout in seconds.
        verify_tls: Whether to verify TLS certificates.

    Returns:
        The detected network state.
    """
    try:
        info = get_portal_info(
            redirect_url=redirect_url,
            timeout=timeout,
            verify_tls=verify_tls,
        )
    except (requests.Timeout, requests.RequestException, ValueError):
        return NetworkState.UNKNOWN
    portal_url = info.portal_url

    target_url = f"{portal_url}/eportal/redirectortosuccess.jsp"
    authed_url = f"{portal_url}/eportal/./success.jsp"

    try:
        resp = requests.head(
            url=target_url,
            allow_redirects=False,
            timeout=timeout,
            verify=verify_tls,
            proxies={"http": None, "https": None},
        )
    except requests.Timeout:
        return NetworkState.OFF_CAMPUS
    except requests.RequestException:
        return NetworkState.UNKNOWN

    location = resp.headers.get("Location")
    if not location:
        return NetworkState.UNKNOWN

    if location == redirect_url:
        return NetworkState.ON_CAMPUS_UNAUTH

    if location.startswith(authed_url):
        return NetworkState.ON_CAMPUS_AUTH

    return NetworkState.UNKNOWN
