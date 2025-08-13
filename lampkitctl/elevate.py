"""Helpers to elevate commands using ``sudo`` while preserving the venv."""
from __future__ import annotations

import os
import shlex
import shutil
import sys


def resolve_self_executable() -> str:
    """Return the absolute path to the current ``lampkitctl`` executable.

    The lookup prefers the console script referenced by ``sys.argv[0]`` and
    falls back to searching ``PATH``. If neither is available, an empty string
    is returned so the caller can choose a ``python -m`` invocation instead.
    """

    argv0 = os.path.realpath(sys.argv[0])
    if os.path.isfile(argv0) and os.access(argv0, os.X_OK):
        return argv0

    found = shutil.which("lampkitctl")
    if found:
        return os.path.realpath(found)

    return ""


def build_sudo_cmd(full_argv: list[str]) -> list[str]:
    """Prefix ``full_argv`` with ``sudo``.

    Args:
        full_argv: Complete argument vector including executable and all
            subcommands/flags.

    Returns:
        List of command parts suitable for :func:`os.execvp`.
    """

    return ["sudo", *full_argv]


def maybe_reexec_with_sudo(
    argv: list[str], *, non_interactive: bool, dry_run: bool
) -> None:
    """Re-execute the current command under ``sudo`` if not already root.

    In non-interactive mode the function prints guidance and exits with code 2
    instead of prompting. ``dry_run`` bypasses any elevation logic.
    """

    if dry_run:
        return

    try:
        is_root = os.geteuid() == 0
    except AttributeError:  # pragma: no cover - non-POSIX
        is_root = False
    if is_root:
        return

    from .utils import echo_err, is_non_interactive, prompt_yes_no

    if non_interactive or is_non_interactive():
        echo_err(
            "Root privileges required. Re-run with: "
            "sudo $(command -v lampkitctl) …  or sudo /full/path/to/.venv/bin/lampkitctl …"
        )
        raise SystemExit(2)

    proceed = prompt_yes_no("Root required. Re-run with sudo now?", default=True)
    if not proceed:
        raise SystemExit(2)

    exe = resolve_self_executable()
    if exe:
        full = [exe] + argv[1:]
    else:
        full = [sys.executable, "-m", "lampkitctl"] + argv[1:]
    cmd = build_sudo_cmd(full)
    print("Re-running as root:", " ".join(shlex.quote(a) for a in cmd))
    os.execvp(cmd[0], cmd)

