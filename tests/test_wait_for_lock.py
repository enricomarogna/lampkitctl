from lampkitctl import preflight_locks


def test_wait_for_lock_releases(monkeypatch):
    seq = [
        preflight_locks.LockInfo(True, 1, "apt", preflight_locks.LOCK_PATHS[0]),
        preflight_locks.LockInfo(False),
    ]
    monkeypatch.setattr(preflight_locks, "detect_lock", lambda: seq.pop(0))
    monkeypatch.setattr(preflight_locks.time, "sleep", lambda s: None)
    info = preflight_locks.wait_for_lock(timeout=2, tick=0.01)
    assert not info.locked
