from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class _Auth:
    db_root_password: Optional[str] = None
    sudo_password: Optional[str] = None

_AUTH = _Auth()

def get_db_root_password() -> Optional[str]:
    return _AUTH.db_root_password

def set_db_root_password(p: str | None) -> None:
    _AUTH.db_root_password = p

def get_sudo_password() -> Optional[str]:
    return _AUTH.sudo_password

def set_sudo_password(p: str | None) -> None:
    _AUTH.sudo_password = p

def clear() -> None:  # for tests
    _AUTH.db_root_password = None
    _AUTH.sudo_password = None
