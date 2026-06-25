"""
paths: Centralized path construction for project directories and files.

This module provides accessors for derived paths within the project structure.
All path construction is localized here to ensure consistency and avoid
scattered path joins throughout the codebase.

Path hierarchy:
    execroot/                        <- execution root (where CLI is invoked)
        <project_dir>/               <- project directory (e.g., ".mytool")
            config.json              <- persistent configuration file

Path resolution modes (for get_path):
    c - configured: Resolve via ctx['path.<id>']
    p - project: Resolve relative to project root directory
    e - execution_root: Resolve relative to execution root
    f - filesystem: Treat id as literal path (cwd-relative if not absolute)
"""

from pathlib import Path
from lionscliapp.execroot import get_execroot
from lionscliapp.application import application


def get_project_root():
    """
    Return the absolute path to the project directory.

    The project directory is <execroot>/<project_dir>, where project_dir
    is declared via application.names.project_dir.

    Returns:
        Path: Absolute path to the project directory

    Raises:
        RuntimeError: If execroot has not been initialized
    """
    return get_execroot() / application["names"]["project_dir"]


def get_config_path():
    """
    Return the absolute path to the project's config.json file.

    Returns:
        Path: Absolute path to config.json within the project directory

    Raises:
        RuntimeError: If execroot has not been initialized
    """
    return get_project_root() / "config.json"


def get_lock_path():
    """
    Return the absolute path to the project's lock.json file.

    Returns:
        Path: Absolute path to lock.json within the project directory

    Raises:
        RuntimeError: If execroot has not been initialized
    """
    return get_project_root() / "lock.json"


def get_instance_path():
    """
    Return the absolute path to the project's instance.json file.

    This file is used by the Tkinter single-instance subsystem to track
    the active GUI owner.
    """
    return get_project_root() / "instance.json"


def get_inbox_path():
    """
    Return the absolute path to the project's inbox/ directory.

    This directory acts as a FileTalk-style mailbox for JSON messages
    destined for the active instance.
    """
    return get_project_root() / "inbox"


def ensure_project_root_exists():
    """
    Create the project directory if it does not exist.

    Uses get_project_root() to determine the path, then creates the
    directory (and any missing parents) if needed.

    Returns:
        Path: The project directory path

    Raises:
        RuntimeError: If execroot has not been initialized
    """
    project_root = get_project_root()
    project_root.mkdir(parents=True, exist_ok=True)
    return project_root


# Valid path mode flags
PATH_MODES = frozenset("cpef")


def get_path(id: str, mode: str = "c") -> Path:
    """
    Resolve a path using the specified mode.

    Args:
        id: Path identifier or literal path (depending on mode)
        mode: Path resolution mode flag:
            'c' - configured: Resolve via ctx['path.<id>']
            'p' - project: Resolve <id> relative to project root
            'e' - execution_root: Resolve <id> relative to execution root
            'f' - filesystem: Treat <id> as literal path (cwd-relative if not absolute)

    Returns:
        Path: The resolved absolute path.

    Raises:
        ValueError: If mode is invalid.
        KeyError: If mode is 'c' and path.<id> is not in ctx.
    """
    if mode not in PATH_MODES:
        raise ValueError(
            f"Invalid path mode: {mode!r}. Must be one of: c, p, e, f"
        )

    if mode == "c":
        return _resolve_configured(id)
    elif mode == "p":
        return _resolve_project(id)
    elif mode == "e":
        return _resolve_execroot(id)
    elif mode == "f":
        return _resolve_filesystem(id)


def _resolve_configured(id: str) -> Path:
    """Resolve path via ctx['path.<id>']."""
    from lionscliapp.ctx import ctx

    key = f"path.{id}"
    if key not in ctx:
        raise KeyError(f"No path configured for '{id}': declare 'path.{id}'")
    return ctx[key]


def _resolve_project(id: str) -> Path:
    """Resolve path relative to project root."""
    p = Path(id)
    if p.is_absolute():
        return p
    return get_project_root() / p


def _resolve_execroot(id: str) -> Path:
    """Resolve path relative to execution root."""
    p = Path(id)
    if p.is_absolute():
        return p
    return get_execroot() / p


def _resolve_filesystem(id: str) -> Path:
    """Treat id as literal path (cwd-relative if not absolute)."""
    p = Path(id)
    if p.is_absolute():
        return p
    return Path.cwd() / p
