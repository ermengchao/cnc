from cnc.client import StateStore


def test_state_store_roundtrip(tmp_path):
    store = StateStore(tmp_path, "state.yaml")
    store.save({"portal_url": "http://portal", "updated_at": 123})

    data = store.load()
    assert data["portal_url"] == "http://portal"
    assert data["updated_at"] == 123
