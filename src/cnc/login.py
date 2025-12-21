import requests

from portal_discovery import get_portal_url, get_query_string


class LoginError(Exception):
    """Raised when portal login fails."""


def login(userId: str, password: str, service: str) -> None:
    portalUrl = get_portal_url()

    queryString = get_query_string()

    url = f"{portalUrl}/eportal/InterFace.do?method=login"

    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    queryString = queryString

    payload = {
        "userId": userId,
        "password": password,
        "service": service,
        "queryString": queryString,
        "operatorPwd": "",
        "operatorUserId": "",
        "validcode": "",
        "passwordEncrypt": "false",
    }

    timeout = 5

    try:
        response = requests.post(
            url=url, headers=headers, data=payload, timeout=timeout
        )
        response.encoding = "utf-8"
        resp_json = response.json()
    except Exception as e:
        raise LoginError(f"request/json decode failed: {e}") from e

    result = resp_json.get("result")
    message = resp_json.get("message", "")

    if result == "success":
        return resp_json
    elif result == "fail":
        raise LoginError(message or "login failed")
    else:
        raise LoginError(f"unknown response: {resp_json}")
