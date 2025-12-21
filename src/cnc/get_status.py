import requests

from get_portal_info import get_portal_info

def get_status(timeout: number = 2):
    """
    curl -I http://10.254.241.19/eportal/redirectortosuccess.jsp
    返回的 Location：
    http://10.254.241.19/eportal/./success.jsp?userIndex=39313436633433373663613464346162396136376139383434663862633136645f31302e31382e3232342e365f32303233303833303631（login）

    http://123.123.123.123/
    logout
    """
    portalUrl, _ = get_portal_info()

    url = f"{portalUrl}/eportal/redirectortosuccess.jsp"

    r = requests.post(
        url = url,
        timeout = timeout
    )


