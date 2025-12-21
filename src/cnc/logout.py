import requests


class LogoutError(Exception):
    """Raised when portal logout fails."""


def logout(portal_url: str) -> None:
    url = f"http://{portal_url}/eportal/InterFace.do?method=logout"

    try:
        response = requests.post(url, timeout=5)
    except Exception as e:
        raise LogoutError(f"request failed: {e}") from e

    if response.status_code != 200:
        raise LogoutError(f"unexpected status code: {response.status_code}")

