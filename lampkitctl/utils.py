"""Utility functions for lampkitctl."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import click
from shutil import get_terminal_size

try:  # pragma: no cover - optional dependency
    from InquirerPy import inquirer
except Exception:  # pragma: no cover - gracefully handle absence
    inquirer = None


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

SECRET_PLACEHOLDER = "****"


def mask_secret(s: str | None) -> str:
    """Return ``SECRET_PLACEHOLDER`` when ``s`` is truthy."""

    return SECRET_PLACEHOLDER if s else ""


def run_command(
    cmd: List[str],
    dry_run: bool = False,
    check: bool = True,
    log_cmd: Optional[Iterable[str]] = None,
    capture_output: bool = False,
    text: bool = True,
    input_text: str | None = None,
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
            input=input_text,
            **kwargs,
        )
    except subprocess.CalledProcessError as exc:
        msg = classify_apt_error(exc)
        print(msg)
        raise SystemExit(2)


def classify_apt_error(e: subprocess.CalledProcessError) -> str:
    """Return a friendly diagnostic for ``apt`` failures."""

    out = "\n".join(filter(None, [e.stdout, e.stderr]))

    def has(text: str) -> bool:
        return text.lower() in out.lower()

    if has("unable to locate package") or has("has no installation candidate"):
        return (
            "APT failed: package not found.\n"
            "- Run: sudo apt-get update\n"
            "- Ensure your Ubuntu release is supported.\n"
            "- If MySQL isn't available, try '--db-engine mariadb'."
        )
    if has("could not get lock") or has("unable to lock"):
        return (
            "APT is locked by another process.\n"
            "- Close apt/dpkg or wait for unattended-upgrades.\n"
            "- Retry with '--wait-apt-lock <seconds>'.\n"
            "- Inspect: ps aux | egrep 'apt|dpkg'"
        )
    if has("temporary failure resolving"):
        return (
            "Network/DNS error while contacting mirrors.\n"
            "- Check internet connectivity and DNS.\n"
            "- Retry: sudo apt-get update"
        )
    if e.returncode == 100 and has("permission denied"):
        return "APT failed due to permissions. Run with sudo or as root."
    snippet = out.strip().splitlines()[-10:]
    return "Command failed (apt):\n" + "\n".join(snippet)


def atomic_append(path: str | Path, content: str) -> None:
    """Append ``content`` to ``path`` atomically.

    The original file mode is preserved. ``content`` is appended to a temporary
    file which is then moved into place using :func:`os.replace`.
    """

    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        existing = p.read_text(encoding="utf-8")
        mode = p.stat().st_mode
    except FileNotFoundError:
        existing = ""
        mode = 0o644
    tmp.write_text(existing + content, encoding="utf-8")
    os.chmod(tmp, mode)
    os.replace(tmp, p)


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


def prompt_yes_no(message: str, default: bool = False) -> bool:
    """Prompt the user for a yes/no response.

    This is a thin wrapper around :func:`prompt_confirm` for semantic clarity.

    Args:
        message: Prompt to display.
        default: Default value when the user presses enter.

    Returns:
        ``True`` if the user confirms, ``False`` otherwise.
    """

    return prompt_confirm(message, default=default)


def ask_confirm(msg: str, default: bool = False) -> bool:
    """Prompt the user for confirmation returning a boolean.

    This helper centralizes confirmation prompts using ``InquirerPy`` when
    available and falling back to :func:`prompt_confirm` otherwise.
    """

    if inquirer:  # pragma: no cover - optional dependency
        return bool(inquirer.confirm(message=msg, default=default).execute())
    return prompt_confirm(msg, default=default)


def echo_err(message: str) -> None:
    """Print ``message`` to standard error."""

    print(message, file=sys.stderr)


# Colored output helpers
def echo_error(msg: str) -> None:
    click.secho(msg, fg="red", bold=True)


def echo_warn(msg: str) -> None:
    click.secho(msg, fg="yellow")


def echo_info(msg: str) -> None:
    click.secho(msg, fg="cyan")


def echo_ok(msg: str) -> None:
    click.secho(msg, fg="green")


def echo_title(msg: str) -> None:
    click.secho(msg, fg="magenta", bold=True)


def is_non_interactive() -> bool:
    """Return ``True`` if stdin is not attached to a TTY."""

    return not sys.stdin.isatty()


def _format_site_line(domain: str, docroot: str) -> str:
    return f"{domain}  ->  {docroot}"


_DEF_EMPTY = "No sites found"


def render_sites_list(sites: list[tuple[str, str]], *, color: bool = True) -> None:
    """Render a list of sites with framing and color.

    Args:
        sites: List of ``(domain, docroot)`` tuples.
        color: If ``True`` use colored output.
    """

    if not sites:
        msg = _DEF_EMPTY
        if color:
            click.secho(msg, fg="red", bold=True)
        else:
            click.echo(msg)
        return

    lines = [_format_site_line(d, r) for d, r in sites]
    max_len = max(len(s) for s in lines)

    term_w = get_terminal_size((80, 20)).columns
    frame_len = max_len
    if frame_len > term_w:
        frame_len = term_w
    frame = "-" * frame_len

    def out(s: str, *, bold: bool = False) -> None:
        if color:
            click.secho(s, fg="green", bold=bold)
        else:
            click.echo(s)

    click.echo()
    out(frame)
    for s in lines:
        out(s, bold=True)
    out(frame)
    click.echo()
