"""Utility functions for lampkitctl."""
from __future__ import annotations

import json
import logging
import subprocess
from typing import Iterable, List, Optional


class JsonFormatter(logging.Formatter):
    """Format log records as JSON strings.

    This formatter converts :class:`logging.LogRecord` instances into JSON
    objects, including extra attributes attached to the record.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Return the log record as a JSON string.

        Args:
            record (logging.LogRecord): Record to format.

        Returns:
            str: JSON representation of the log record.

        Example:
            >>> logger = logging.getLogger(__name__)
            >>> logger.addHandler(logging.StreamHandler())
            >>> logger.handlers[0].setFormatter(JsonFormatter())
            >>> logger.info("hello")
            {"level": "INFO", ...}
        """
        data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        for key, value in getattr(record, "__dict__", {}).items():
            if key not in {
                "levelname",
                "msg",
                "args",
                "name",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                data[key] = value
        return json.dumps(data)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a JSON formatter.

    Args:
        level (int, optional): Logging level for the root logger. Defaults to
            :data:`logging.INFO`.

    Returns:
        None: This function does not return a value.

    Example:
        >>> setup_logging()
        >>> logging.getLogger(__name__).info("hi")
        {"level": "INFO", ...}
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)


logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    dry_run: bool = False,
    check: bool = True,
    log_cmd: Optional[Iterable[str]] = None,
    capture_output: bool = False,
    text: bool = True,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Execute a system command with logging and optional dry run.

    Args:
        cmd (List[str]): Command and arguments to execute.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.
        check (bool, optional): If ``True`` raise
            :class:`subprocess.CalledProcessError` on non-zero exit. Defaults
            to ``True``.
        log_cmd (Optional[Iterable[str]], optional): Alternate command to log
            instead of ``cmd``. Defaults to ``None``.
        **kwargs: Additional arguments passed to :func:`subprocess.run`.

    Returns:
        subprocess.CompletedProcess: Result of the executed command or a dummy
            instance when ``dry_run`` is ``True``.

    Example:
        >>> run_command(["echo", "hi"], dry_run=True)
        CompletedProcess(args=['echo', 'hi'], returncode=0)
    """
    logger.info("run_command", extra={"cmd": list(log_cmd or cmd), "dry_run": dry_run})
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs,
        )
    except subprocess.CalledProcessError as exc:
        msg = classify_apt_error(exc)
        print(msg)
        raise SystemExit(2)


def classify_apt_error(e: subprocess.CalledProcessError) -> str:
    """Return a friendly diagnostic for ``apt`` failures."""

    out = "".join([e.stdout or "", "\n", e.stderr or ""]).strip()
    if "Permission denied" in out or e.returncode in (100,):
        return (
            "APT failed (permission/lock).\n"
            "- Ensure you run as root: sudo ...\n"
            "- Close other package managers (apt/dpkg).\n"
            "- Retry: sudo apt-get update && sudo apt-get install ..."
        )
    if "Could not get lock" in out or "Unable to lock" in out:
        return (
            "APT lock is held by another process. Close Software Updater/apt and retry.\n"
            "Tip: check 'ps aux | grep apt'"
        )
    return f"Command failed: {e.cmd} (exit {e.returncode})\n{out}".strip()


def prompt_confirm(message: str, default: bool = False) -> bool:
    """Prompt the user for a yes/no confirmation.

    Args:
        message (str): Message to display to the user.
        default (bool, optional): Default response if the user presses enter
            without typing anything. Defaults to ``False``.

    Returns:
        bool: ``True`` if the user confirms, ``False`` otherwise.

    Example:
        >>> # Assuming user types 'y'
        >>> prompt_confirm('Proceed?')
        True
    """
    prompt = " [Y/n]: " if default else " [y/N]: "
    while True:
        resp = input(message + prompt).strip().lower()
        if not resp:
            return default
        if resp in {"y", "yes"}:
            return True
        if resp in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")
