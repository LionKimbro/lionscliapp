"""
resolve_execroot: Execution root resolution logic.

Determines the execution root directory based on:
1. CLI override (if allowed and provided)
2. Current working directory (default)
3. Upward search for project directory (if enabled)

This module reads global state but does not perform filesystem writes.
It calls execroot.set_execroot() exactly once.
"""

from pathlib import Path

from lionscliapp.application import application
from lionscliapp.execroot import set_execroot
from lionscliapp.cli_state import g as cli_state_g


def resolve_execroot():
    """
    Resolve and set the execution root directory.

    Resolution order:
    1. If allow_execroot_override is true and cli_state has an override, use it
    2. Otherwise, start with current working directory
    3. If search_upwards_for_project_dir is true, search parent directories

    Calls execroot.set_execroot() exactly once with the resolved path.

    Raises:
        RuntimeError: If execroot has already been set
        ValueError: If CLI override provided but not allowed
    """
    cli_override = cli_state_g["execroot_override"]
    allow_override = application["flags"]["allow_execroot_override"]

    if cli_override is not None:
        if not allow_override:
            raise ValueError(
                "execroot override provided but "
                "application.flags.allow_execroot_override is false"
            )
        set_execroot(Path(cli_override))
        return

    execroot = Path.cwd()

    if application["flags"]["search_upwards_for_project_dir"]:
        project_dir = application["names"]["project_dir"]
        found = _search_upwards_for_project_dir(execroot, project_dir)
        if found is not None:
            execroot = found

    set_execroot(execroot)


def _search_upwards_for_project_dir(start, project_dir):
    """
    Search parent directories for an existing project directory.

    Args:
        start: Starting directory path
        project_dir: Name of project directory to find

    Returns:
        Path: Directory containing the project directory, or None if not found
    """
    current = start.resolve()

    while True:
        candidate = current / project_dir
        if candidate.is_dir():
            return current

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent
