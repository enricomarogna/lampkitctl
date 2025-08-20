from lampkitctl import system_ops
from lampkitctl.packages import Engine
from lampkitctl import preflight_locks


def test_update_before_detection(monkeypatch):
    calls = []

    def fake_refresh(**kwargs):
        calls.append("update")

    def fake_detect(preferred):
        calls.append("detect")
        return Engine("mysql", "mysql-server", "mysql-client", "mysql")

    def fake_run(cmd, dry_run=False, capture_output=False):
        calls.append(cmd)

    monkeypatch.setattr(system_ops, "refresh_cache", fake_refresh)
    monkeypatch.setattr(system_ops, "detect_db_engine", fake_detect)
    monkeypatch.setattr(system_ops, "run_command", fake_run)
    monkeypatch.setattr(system_ops.preflight_locks, "detect_lock", lambda: preflight_locks.LockInfo(False))

    system_ops.install_lamp_stack_full(None, dry_run=True)

    assert calls[0:2] == ["update", "detect"]
    install_cmd = calls[2]
    assert install_cmd[0:3] == ["apt-get", "install", "-y"]
    assert "--no-install-recommends" in install_cmd
    assert "mysql-server" in install_cmd

