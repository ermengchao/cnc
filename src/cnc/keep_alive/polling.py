from __future__ import annotations

import time

from cnc.login import login, LoginError
from cnc.logout import logout, LogoutError


class KeepAliveError(Exception):
    """Raised when keep-alive loop cannot continue."""


def run(*, test_func, interval_seconds: int = 300) -> None:
    """
    策略 v1：每隔 interval_seconds 检测一次是否在线；不在线就报错退出/抛异常。
    test_func: 由 main.py 注入（避免 keep_logged_in 依赖你的 test 模块细节）
              约定返回 1=在线, 0=离线, 其他=异常
    """
    while True:
        result = test_func()
        if result == 1:
            time.sleep(interval_seconds)
            continue
        raise KeepAliveError("keep_logged_in_v1: offline or unexpected network status")
