"""Utility functions for lampkitctl."""
from __future__ import annotations

import json
import logging
import subprocess
from typing import Iterable, List, Optional


class JsonFormatter(logging.Formatter):
    """Simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        for key, value in getattr(record, "__dict__", {}).items():
            if key not in {"levelname", "msg", "args", "name", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}:
                data[key] = value
        return json.dumps(data)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)


logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    dry_run: bool = False,
    check: bool = True,
    log_cmd: Optional[Iterable[str]] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Execute a system command with logging and optional dry-run.

    Args:
        cmd: Command and arguments to execute.
        dry_run: If ``True`` the command is logged but not executed.
        check: If ``True`` raise :class:`subprocess.CalledProcessError` on error.
        log_cmd: Optional command representation to log instead of ``cmd``.

    Returns:
        :class:`subprocess.CompletedProcess` representing the result.
    """
    logger.info("run_command", extra={"cmd": list(log_cmd or cmd), "dry_run": dry_run})
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, check=check, text=True, **kwargs)


def prompt_confirm(message: str, default: bool = False) -> bool:
    """Prompt the user for confirmation."""
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
