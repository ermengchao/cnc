from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


"""
Retrieve the campus network portal base URL and authentication query string
from an unauthenticated redirection response.

In a typical campus network environment, when a device is already connected
to the network but has not yet completed authentication, accessing a fixed
redirection URL (e.g. ``http://123.123.123.123``) returns an HTML page
containing a JavaScript-based redirect, such as::

    <script>
        top.self.location.href='http://10.254.241.19/eportal/index.jsp?'
        'wlanuserip=...&wlanacname=...&...'
    </script>

This JavaScript snippet embeds:
1. The **portal base URL** (e.g. ``http://10.254.241.19``), and
2. The **query string** required for subsequent authentication requests.

This function performs an HTTP GET request to the given ``redirect_url``,
extracts the redirection URL from the JavaScript code, validates it, and
returns:
- the portal base URL (scheme + netloc), and
- the full query string used for authentication.

The extracted information is intended to be consumed by the login/authentication
module as a prerequisite for completing the campus network login flow.

Args:
    redirect_url (str, optional):
        The redirection URL provided by the campus network. Defaults to
        ``"http://123.123.123.123/"``.
    timeout (float, optional):
        Timeout (in seconds) for the HTTP request. Defaults to ``8.0``.
    verify_tls (bool, optional):
        Whether to verify TLS certificates for HTTPS requests. Defaults to
        ``False``.

Returns:
    Tuple[str, str]:
        A tuple consisting of:
        - the portal base URL (e.g. ``"http://10.254.241.19"``), and
        - the authentication query string extracted from the redirect URL.

Raises:
    requests.HTTPError:
        If the HTTP request fails or returns a non-success status code.
    ValueError:
        If no redirection URL can be found in the response, or if the extracted
        URL is malformed or incomplete.
"""
@dataclass(frozen=True)
class PortalInfo:
    base_url: str
    query_string: str
    full_url: str


def fetch_portal_html(
    redirect_url: str,
    *,
    timeout: float = 8.0,
    verify_tls: bool = False,
) -> str:
    resp = requests.get(
        redirect_url,
        timeout=timeout,
        verify=verify_tls,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/26.2 Safari/605.1.15"
            )
        },
    )
    resp.raise_for_status()
    return resp.text


def extract_redirect_url(html: str) -> str:
    m = re.search(
        r"""location\.href\s*=\s*['"]([^'"]+)['"]""",
        html,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError("Error: Can not find portal url.")

    return m.group(1).replace("\n", "").replace("\r", "").strip()


def parse_portal_info(full_url: str) -> PortalInfo:
    parsed = urlparse(full_url)
    if not parsed.scheme or not parsed.netloc or not parsed.query:
        raise ValueError(f"Error: Illegal url: {full_url}")

    base = f"{parsed.scheme}://{parsed.netloc}"
    return PortalInfo(base_url=base, query_string=parsed.query, full_url=full_url)


def get_portal_info(
    redirect_url: str = "http://123.123.123.123/",
    *,
    timeout: float = 8.0,
    verify_tls: bool = False,
) -> PortalInfo:
    html = fetch_portal_html(redirect_url, timeout=timeout, verify_tls=verify_tls)
    full = extract_redirect_url(html)
    return parse_portal_info(full)


def get_portal_url(
    redirect_url: str = "http://123.123.123.123/",
    *,
    timeout: float = 8.0,
    verify_tls: bool = False,
) -> str:
    return get_portal_info(
        redirect_url, timeout=timeout, verify_tls=verify_tls
    ).base_url


def get_query_string(
    redirect_url: str = "http://123.123.123.123/",
    *,
    timeout: float = 8.0,
    verify_tls: bool = False,
) -> str:
    return get_portal_info(
        redirect_url, timeout=timeout, verify_tls=verify_tls
    ).query_string

# from __future__ import annotations
#
# import re
#
# from urllib.parse import urlparse
# from typing import Tuple
#
# import requests
#
#
# def get_portal_info(
#     redirect_url: str = "http://123.123.123.123/",
#     *,
#     timeout: float = 8.0,
#     verify_tls: bool = False,
# ) -> Tuple[str, str]:
#     resp = requests.get(
#         redirect_url,
#         timeout=timeout,
#         verify=verify_tls,
#         headers={
#             "User-Agent": (
#                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
#                 "AppleWebKit/605.1.15 (KHTML, like Gecko) "
#                 "Version/26.2 Safari/605.1.15"
#             )
#         },
#     )
#     resp.raise_for_status()
#
#     html = resp.text
#
#     m = re.search(
#         r"""location\.href\s*=\s*['"]([^'"]+)['"]""",
#         html,
#         flags=re.IGNORECASE,
#     )
#     if not m:
#         raise ValueError("Error: Can not find portal url.")
#
#     full_url = m.group(1).replace("\n", "").replace("\r", "").strip()
#
#     parsed = urlparse(full_url)
#
#     if not parsed.scheme or not parsed.netloc or not parsed.query:
#         raise ValueError(f"Error: Illegal url: {full_url}")
#
#     return (f"{parsed.scheme}://{parsed.netloc}", parsed.query)
