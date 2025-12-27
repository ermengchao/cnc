from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult

import requests


@dataclass(frozen=True)
class PortalInfo:
    """
    Container for portal redirection information extracted from
    a captive portal redirect response.
    """

    full_url: str
    parsed: ParseResult

    @property
    def portal_url(self) -> str:
        """
        Return the base portal URL without query parameters.

        Example:
            http://10.254.241.19

        Returns:
            Portal base URL.
        """
        return f"{self.parsed.scheme}://{self.parsed.netloc}"

    @property
    def query_string(self) -> str:
        """
        Return the raw query string required for authentication.

        Returns:
            The raw query string.
        """
        return self.parsed.query

    @property
    def full_portal_url(self) -> str:
        """
        Return the full portal URL including query parameters.

        Returns:
            The full portal URL with query parameters.
        """
        return self.full_url


def get_portal_info(
    redirect_url: str = "http://123.123.123.123/",
    *,
    timeout: float = 2.0,
    verify_tls: bool = False,
) -> PortalInfo:
    """
    Fetch a redirection page and extract captive portal information.

    This function performs an HTTP GET request to a known redirection
    address. When the network is unauthenticated, the response is
    expected to contain a JavaScript snippet that redirects the client
    to the campus portal login page.

    Args:
        redirect_url:
            URL used to trigger captive portal redirection.
        timeout:
            Request timeout in seconds.
        verify_tls:
            Whether to verify TLS certificates.

    Returns:
        A PortalInfo instance containing the parsed portal URL
        and authentication query string.

    Raises:
        requests.RequestException:
            If the HTTP request fails.
        ValueError:
            If the portal URL cannot be found or is malformed.
    """
    resp = requests.get(
        redirect_url,
        timeout=timeout,
        verify=verify_tls,
        proxies={"http": None, "https": None},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/26.2 Safari/605.1.15"
            )
        },
    )
    resp.raise_for_status()

    html = resp.text

    match = re.search(
        r"""location\.href\s*=\s*['"]([^'"]+)['"]""",
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError("Unable to locate portal redirection URL.")

    full_url = match.group(1).replace("\n", "").replace("\r", "").strip()

    parsed = urlparse(full_url)

    if not parsed.scheme or not parsed.netloc or not parsed.query:
        raise ValueError(f"Malformed portal URL: {full_url}")

    return PortalInfo(
        full_url=full_url,
        parsed=parsed,
    )
