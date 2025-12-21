from __future__ import annotations

import time
import schedule

from cnc.login import login, LoginError
from cnc.logout import logout, LogoutError


class KeepAliveError(Exception):
    """Raised when keep-alive loop cannot continue."""


def run(
    *,
    userId: str,
    password: str,
    service: str,
    portalUrl: str,
    logout_at: str = "05:00",
) -> None:
    """
    策略 v2：每天固定时间先登出再登入。
    logout_at: "HH:MM" 24小时制
    """

    def _do_logout_then_login():
        try:
            logout(portalUrl)
        except LogoutError:
            # 登出失败通常不致命，继续尝试登录
            pass
        login(userId, password, service, portalUrl)

    # 启动时先登录一次（可选）
    login(userId, password, service, portalUrl)

    schedule.clear()
    schedule.every().day.at(logout_at).do(_do_logout_then_login)

    while True:
        schedule.run_pending()
        time.sleep(1)
