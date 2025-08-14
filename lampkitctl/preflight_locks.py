from __future__ import annotations

"""Helpers for detecting and waiting on APT/dpkg lock files."""

from dataclasses import dataclass
from typing import Optional, Callable
import subprocess
import time

LOCK_PATHS = [
    "/var/lib/dpkg/lock-frontend",
    "/var/lib/dpkg/lock",
    "/var/lib/apt/lists/lock",
]


@dataclass
class LockInfo:
    """Information about a detected lock."""

    locked: bool
    holder_pid: Optional[int] = None
    holder_cmd: Optional[str] = None
    path: Optional[str] = None
    raw: str = ""


_DEF_LSLOCKS = ["lslocks", "-o", "PID,COMMAND,PATH"]


def _run(cmd: list[str]) -> tuple[int, str]:
    """Return ``(returncode, combined_output)`` for ``cmd``."""

    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def detect_lock() -> LockInfo:
    """Return information about any active APT/dpkg lock."""

    code, out = _run(_DEF_LSLOCKS)
    if code == 0 and out:
        for line in out.splitlines():
            parts = [x.strip() for x in line.split()]
            if len(parts) >= 3:
                pid, cmd, path = parts[0], parts[1], parts[2]
                if path in LOCK_PATHS:
                    try:
                        return LockInfo(True, int(pid), cmd, path, out)
                    except ValueError:
                        pass
    code, out = _run(["lsof", "-FnPc", *LOCK_PATHS])
    if code == 0 and out:
        pid: Optional[int] = None
        cmd: Optional[str] = None
        path: Optional[str] = None
        for tok in out.splitlines():
            if tok.startswith("p"):
                try:
                    pid = int(tok[1:])
                except ValueError:
                    pid = None
            elif tok.startswith("c"):
                cmd = tok[1:]
            elif tok.startswith("n"):
                path = tok[1:]
                if path in LOCK_PATHS and pid is not None:
                    return LockInfo(True, pid, cmd, path, out)
    code, out = _run(["bash", "-lc", "fuser -v " + " ".join(LOCK_PATHS)])
    if code == 0 and any(p in out for p in LOCK_PATHS):
        return LockInfo(True, None, None, None, out)
    return LockInfo(False, raw=out)


def wait_for_lock(
    timeout: int,
    tick: float = 1.0,
    on_progress: Optional[Callable[[LockInfo], None]] = None,
) -> LockInfo:
    """Wait for any APT/dpkg lock to clear up to ``timeout`` seconds."""

    end = time.time() + max(0, timeout)
    last: Optional[LockInfo] = None
    while time.time() < end:
        info = detect_lock()
        if not info.locked:
            return info
        if on_progress and (last is None or info != last):
            on_progress(info)
        time.sleep(tick)
        last = info
    return detect_lock()

