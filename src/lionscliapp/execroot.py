"""
execroot: Execution root directory management.

The execroot is the directory from which the CLI tool is invoked.
It serves as the base for locating the project directory and config files.

This module holds the execroot as global state. It is set once during
startup and remains constant for the duration of execution.

The global is stored in a dict and manipulated in-place per project conventions.
"""

from pathlib import Path

g = {"execroot": None}  # Path | None


def set_execroot(p):
    """
    Set the execution root directory.

    May only be called once per execution lifecycle.

    Args:
        p: Path to the execution root directory

    Raises:
        RuntimeError: If execroot has already been set
    """
    if g["execroot"] is not None:
        raise RuntimeError("execroot already set")
    g["execroot"] = p


def get_execroot():
    """
    Get the execution root directory.

    Returns:
        Path: The execution root directory

    Raises:
        RuntimeError: If execroot has not been initialized
    """
    if g["execroot"] is None:
        raise RuntimeError("execroot not initialized")
    return g["execroot"]


def reset_execroot():
    """
    Reset execroot to uninitialized state.

    Intended for tests and controlled reset scenarios.
    """
    g["execroot"] = None

