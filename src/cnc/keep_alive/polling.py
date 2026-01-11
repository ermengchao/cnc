import time
import logging

from cnc.client import (
    CampusNetClient,
    NetworkState,
    NeedUnauthed,
    AlreadyOnline,
    AlreadyOffline,
)

log = logging.getLogger(__name__)


def run(
    *,
    user_id: str,
    password: str,
    service: str,
    interval_seconds: int = 300,
    portal_url: str | None = None,
) -> None:
    """
    Polling keep-alive loop.

    Strategy:
    - Ensure portal_url state exists (or discover it if possible)
    - Loop forever:
        - Detect NetworkState via client.status()
        - If ON_CAMPUS_UNAUTH -> attempt login
        - If ON_CAMPUS_AUTH  -> do nothing
        - If OFF_CAMPUS      -> do nothing (sleep and retry)
        - If UNKNOWN         -> do nothing (sleep and retry)
    """
    client = CampusNetClient()

    # 1) Ensure cache / portal_url is ready.
    #    If user passes portal_url, we can write it into state to override.
    if portal_url:
        client.state.save({"portal_url": portal_url, "updated_at": int(time.time())})
    else:
        try:
            client.ensure_state()
        except NeedUnauthed:
            log.warning("State missing/expired but already authenticated; cannot auto-discover portal_url now.")

    # 2) Main loop
    while True:
        try:
            st = client.status()
        except Exception as e:
            log.warning("status check failed: %s", e)
            time.sleep(interval_seconds)
            continue

        if st == NetworkState.ON_CAMPUS_AUTH:
            log.debug("already authenticated")
            time.sleep(interval_seconds)
            continue

        if st == NetworkState.ON_CAMPUS_UNAUTH:
            log.info("on campus but unauthenticated; trying to login...")
            try:
                client.login(user_id=user_id, password=password, service=service)
            except AlreadyOnline:
                log.debug("login skipped: already online")
            except AlreadyOffline:
                log.info("login skipped: appears offline")
            except Exception as e:
                log.warning("login failed: %s", e)

            time.sleep(interval_seconds)
            continue

        if st == NetworkState.OFF_CAMPUS:
            log.info("off campus; nothing to do")
            time.sleep(interval_seconds)
            continue

        # NetworkState.UNKNOWN or any future state
        log.debug("unknown state: %s", st)
        time.sleep(interval_seconds)
