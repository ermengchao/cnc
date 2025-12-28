from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests
import os

from cnc.portal import get_portal_info
from cnc.probe import NetworkState, detect_network_status
from cnc.login import do_login, LoginError
from cnc.logout import do_logout, LogoutError


class StateError(RuntimeError):
    """Raised when state cannot be loaded/saved or is missing when required."""


class NeedUnauthed(RuntimeError):
    """Raised when an operation requires the user to be on-campus but unauthenticated."""


class AlreadyOnline(RuntimeError):
    """Raised when an operation is skipped because the user is already online."""


class AlreadyOffline(RuntimeError):
    """Raised when an operation is skipped because the user is already offline."""


def get_state_dir() -> Path:
    """Return the directory used to store cnc state files.

    Returns:
        The directory path used for state storage.
    """
    if xdg := os.environ.get("XDG_STATE_HOME"):
        return Path(xdg) / "cnc"

    local_share = Path.home() / ".local" / "share"
    if local_share.exists():
        return local_share / "cnc"

    return Path(".")


@dataclass(frozen=True)
class ClientConfig:
    """
    Configuration for CampusNetClient.
    """

    redirect_url: str = "http://123.123.123.123/"
    timeout: float = 2.0
    verify_tls: bool = False

    state_dir: Path = field(default_factory=get_state_dir)
    state_file: str = "state.yaml"

    # Best-effort freshness window for portal_url cache.
    state_ttl_seconds: int = 30 * 60  # 30 minutes

    # Logout request timeout.
    logout_timeout: float = 2.0


class StateStore:
    """
    Minimal YAML-like state store.

    The file format is intentionally simple to avoid extra dependencies:
        portal_url: http://10.254.241.19
        updated_at: 1700000000
    """

    def __init__(self, state_dir: Path, filename: str) -> None:
        """Create a state store rooted at the given directory.

        Args:
            state_dir: Directory to store the state file.
            filename: Name of the state file.

        Returns:
            None.
        """
        self._dir = state_dir
        self._path = state_dir / filename

    @property
    def path(self) -> Path:
        """Return the full path to the state file.

        Returns:
            The full state file path.
        """
        return self._path

    def load(self) -> Optional[dict]:
        """Load the state file into a dict, or return None if missing/empty.

        Returns:
            Parsed state dict, or None if the file is missing/empty.
        """
        if not self._path.exists():
            return None

        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as e:
            raise StateError(f"Failed to read state file: {self._path}: {e}") from e

        data: dict[str, object] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            key = k.strip()
            val = v.strip()
            if key == "updated_at":
                try:
                    data[key] = int(val)
                except ValueError:
                    data[key] = val
            else:
                data[key] = val

        return data or None

    def save(self, data: dict) -> None:
        """Persist the given state dict to disk.

        Args:
            data: State data to write.

        Returns:
            None.
        """
        self._dir.mkdir(parents=True, exist_ok=True)

        payload_lines = []
        for k, v in data.items():
            payload_lines.append(f"{k}: {v}")
        payload = "\n".join(payload_lines) + "\n"

        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(self._path)  # atomic-ish on POSIX
        except OSError as e:
            raise StateError(f"Failed to write state file: {self._path}: {e}") from e


class CampusNetClient:
    """
    Orchestration layer for cnc.

    Responsibilities:
    - Ensure portal_url state exists when possible (only discoverable when unauthenticated).
    - Persist portal_url to ~/.local/state/cnc/state.yaml.
    - Execute login/logout flows using existing cnc modules.
    """

    def __init__(
        self,
        *,
        config: ClientConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize a client with optional config and HTTP session.

        Args:
            config: Optional client configuration.
            session: Optional requests session for HTTP calls.

        Returns:
            None.
        """
        self.config = config or ClientConfig()
        self.session = session or requests.Session()
        self.state = StateStore(self.config.state_dir, self.config.state_file)

    def status(self) -> NetworkState:
        """
        Return the current network/authentication state.

        Returns:
            The detected network state.
        """
        cached = self.state.load()
        if not cached or not isinstance(cached.get("portal_url"), str):
            raise StateError(
                "No cached portal_url found. Please run `cnc login` once to "
                "initialize the cache before using other commands."
            )

        st = detect_network_status(
            redirect_url=self.config.redirect_url,
            timeout=min(self.config.timeout, 2.0),
        )
        if st != NetworkState.UNKNOWN:
            return st

        return self._status_from_portal_url(str(cached["portal_url"]))

    def ensure_state(self) -> dict:
        """
        Ensure a usable portal_url exists in the state file.

        Flow (mirrors your flowchart):
        - If state exists and looks fresh enough => use it
        - Else probe:
            - If authed => raise NeedUnauthed (cannot discover portal_url via redirect)
            - If not authed => discover portal info and write state

        Returns:
            Loaded state dict containing at least `portal_url`.

        Raises:
            NeedUnauthed: if user is already authenticated and state is missing/expired.
            StateError: on state read/write errors.
            ValueError/requests exceptions: from portal discovery when unauthenticated.
        """
        cached = self.state.load()
        if self._state_has_fresh_portal_url(cached):
            return cached  # type: ignore[return-value]

        st = self.status()
        if st == NetworkState.ON_CAMPUS_AUTH:
            raise NeedUnauthed(
                "State is missing/expired but you appear to be already authenticated. "
                "Please run this once when unauthenticated so portal_url can be discovered and cached, "
                "or pass --portal-url explicitly for logout."
            )

        # If we're unauthenticated on-campus (or unknown-but-not-authed), try discovery.
        info = get_portal_info(
            self.config.redirect_url,
            timeout=self.config.timeout,
            verify_tls=self.config.verify_tls,
        )

        now = int(time.time())
        data = {
            "portal_url": info.portal_url,
            "updated_at": now,
        }
        self.state.save(data)
        return data

    def login(self, user_id: str, password: str, service: str) -> None:
        """
        Login using the existing cnc.login.do_login implementation.

        Notes:
        - We try to discover portal info here so we can pass portal_url/query_string
          into do_login() and cache portal_url for future logout.

        Args:
            user_id: User identifier for the portal.
            password: User password.
            service: Service name to authenticate against.

        Returns:
            None.

        Raises:
            AlreadyOnline: If the user is already online.
            AlreadyOffline: If the user appears to be offline.
        """
        cached = self.state.load()
        if cached and isinstance(cached.get("portal_url"), str):
            st = self._status_from_portal_url(str(cached["portal_url"]))
        else:
            try:
                st = detect_network_status(
                    redirect_url=self.config.redirect_url,
                    timeout=min(self.config.timeout, 2.0),
                    verify_tls=self.config.verify_tls,
                )
            except Exception:
                st = NetworkState.UNKNOWN

        if st == NetworkState.ON_CAMPUS_AUTH:
            raise AlreadyOnline("Already online. Login skipped.")
        if st == NetworkState.OFF_CAMPUS:
            raise AlreadyOffline("You appear to be offline. Login skipped.")

        portal_url = None
        query_string = None

        try:
            info = get_portal_info(
                self.config.redirect_url,
                timeout=self.config.timeout,
                verify_tls=self.config.verify_tls,
            )
            portal_url = info.portal_url
            query_string = info.query_string
            self.state.save(
                {
                    "portal_url": portal_url,
                    "updated_at": int(time.time()),
                }
            )
        except Exception:
            # Best-effort: if discovery fails, fall back to cached portal_url if available.
            cached = self.state.load()
            if cached and isinstance(cached.get("portal_url"), str):
                portal_url = cached["portal_url"]

        do_login(
            user_id,
            password,
            service,
            portal_url=portal_url,
            query_string=query_string,
            timeout=self.config.timeout,
            verify_tls=self.config.verify_tls,
        )

    def logout(self) -> None:
        """
        Logout using cached portal_url or a fresh portal discovery.

        Raises:
            StateError / NeedUnauthed: if portal_url cannot be determined.
            LogoutError: if the logout request fails.
            AlreadyOffline: if the user is already offline.

        Returns:
            None.
        """
        cached = self.state.load()
        if not cached or not isinstance(cached.get("portal_url"), str):
            raise StateError(
                "No cached portal_url found. Please run `cnc login` once to "
                "initialize the cache before using other commands."
            )

        st = self._status_from_portal_url(str(cached["portal_url"]))
        if st in (NetworkState.ON_CAMPUS_UNAUTH, NetworkState.OFF_CAMPUS):
            raise AlreadyOffline("Already offline. Logout skipped.")
        if st == NetworkState.UNKNOWN:
            raise StateError(
                "Unable to determine current status with cached portal_url. "
                "Please verify your network and try again."
            )

        url = None
        try:
            info = get_portal_info(
                self.config.redirect_url,
                timeout=self.config.logout_timeout,
                verify_tls=self.config.verify_tls,
            )
            url = info.portal_url
            self.state.save(
                {
                    "portal_url": url,
                    "updated_at": int(time.time()),
                }
            )
        except Exception:
            cached = self.state.load()
            if cached and isinstance(cached.get("portal_url"), str):
                url = cached["portal_url"]

        if not url:
            raise StateError(
                "Unable to determine portal_url for logout. "
                "Please run `cnc login` or `cnc status` once when unauthenticated "
                "to cache the portal URL, then retry logout."
            )

        do_logout(
            portal_url=url,
            timeout=self.config.logout_timeout,
            verify_tls=self.config.verify_tls,
        )

    def _state_has_fresh_portal_url(self, data: Optional[dict]) -> bool:
        """Return True if cached portal_url exists and is within TTL.

        Args:
            data: State dict to validate.

        Returns:
            True if portal_url is present and not expired.
        """
        if not data:
            return False
        portal_url = data.get("portal_url")
        updated_at = data.get("updated_at")

        if not isinstance(portal_url, str) or not portal_url.strip():
            return False

        if isinstance(updated_at, int):
            age = int(time.time()) - updated_at
            if age > self.config.state_ttl_seconds:
                return False

        return True

    def _status_from_portal_url(self, portal_url: str) -> NetworkState:
        """Detect network status using a cached portal URL.

        Args:
            portal_url: Portal base URL or host.

        Returns:
            The detected network state.
        """
        if portal_url.startswith("http://") or portal_url.startswith("https://"):
            base_url = portal_url
        else:
            base_url = f"http://{portal_url}"

        target_url = f"{base_url}/eportal/redirectortosuccess.jsp"
        authed_url = f"{base_url}/eportal/./success.jsp"

        try:
            resp = self.session.head(
                url=target_url,
                allow_redirects=False,
                timeout=min(self.config.timeout, 2.0),
                verify=self.config.verify_tls,
                proxies={"http": None, "https": None},
            )
        except requests.Timeout:
            return NetworkState.OFF_CAMPUS
        except requests.RequestException:
            return NetworkState.UNKNOWN

        location = resp.headers.get("Location")
        if not location:
            return NetworkState.UNKNOWN

        if location == self.config.redirect_url:
            return NetworkState.ON_CAMPUS_UNAUTH

        if location.startswith(authed_url):
            return NetworkState.ON_CAMPUS_AUTH

        return NetworkState.UNKNOWN
