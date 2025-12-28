import types
import pytest

from cnc.client import (
    AlreadyOffline,
    AlreadyOnline,
    CampusNetClient,
    ClientConfig,
    StateError,
)
from cnc.probe import NetworkState


def _config(tmp_path):
    return ClientConfig(state_dir=tmp_path)


def test_status_requires_cache(tmp_path):
    client = CampusNetClient(config=_config(tmp_path))
    with pytest.raises(StateError):
        client.status()


def test_status_uses_detect_then_fallback(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    client.state.save({"portal_url": "http://portal", "updated_at": 1})

    monkeypatch.setattr("cnc.client.detect_network_status", lambda **_: NetworkState.UNKNOWN)
    monkeypatch.setattr(client, "_status_from_portal_url", lambda *_: NetworkState.OFF_CAMPUS)

    assert client.status() == NetworkState.OFF_CAMPUS


def test_login_off_campus_raises(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    monkeypatch.setattr("cnc.client.detect_network_status", lambda **_: NetworkState.OFF_CAMPUS)

    with pytest.raises(AlreadyOffline):
        client.login("user", "pass", "电信")


def test_login_already_online_raises(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    client.state.save({"portal_url": "http://portal", "updated_at": 1})
    monkeypatch.setattr(client, "_status_from_portal_url", lambda *_: NetworkState.ON_CAMPUS_AUTH)

    with pytest.raises(AlreadyOnline):
        client.login("user", "pass", "电信")


def test_login_saves_cache_and_calls_do_login(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    monkeypatch.setattr("cnc.client.detect_network_status", lambda **_: NetworkState.ON_CAMPUS_UNAUTH)

    info = types.SimpleNamespace(portal_url="http://portal", query_string="q=1")
    monkeypatch.setattr("cnc.client.get_portal_info", lambda *_, **__: info)

    called = {}

    def _do_login(user_id, password, service, **kwargs):
        called["user_id"] = user_id
        called["password"] = password
        called["service"] = service
        called["portal_url"] = kwargs.get("portal_url")
        called["query_string"] = kwargs.get("query_string")

    monkeypatch.setattr("cnc.client.do_login", _do_login)

    client.login("user", "pass", "电信")

    cached = client.state.load()
    assert cached["portal_url"] == "http://portal"
    assert called["portal_url"] == "http://portal"
    assert called["query_string"] == "q=1"


def test_logout_already_offline_raises(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    client.state.save({"portal_url": "http://portal", "updated_at": 1})
    monkeypatch.setattr(client, "_status_from_portal_url", lambda *_: NetworkState.OFF_CAMPUS)

    with pytest.raises(AlreadyOffline):
        client.logout()


def test_logout_calls_do_logout(tmp_path, monkeypatch):
    client = CampusNetClient(config=_config(tmp_path))
    client.state.save({"portal_url": "http://portal", "updated_at": 1})
    monkeypatch.setattr(client, "_status_from_portal_url", lambda *_: NetworkState.ON_CAMPUS_AUTH)
    monkeypatch.setattr("cnc.client.get_portal_info", lambda *_, **__: (_ for _ in ()).throw(Exception("boom")))

    called = {}

    def _do_logout(*, portal_url, **_):
        called["portal_url"] = portal_url

    monkeypatch.setattr("cnc.client.do_logout", _do_logout)

    client.logout()
    assert called["portal_url"] == "http://portal"
