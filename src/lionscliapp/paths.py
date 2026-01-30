"""
paths: Centralized path construction for project directories and files.

This module provides accessors for derived paths within the project structure.
All path construction is localized here to ensure consistency and avoid
scattered path joins throughout the codebase.

Path hierarchy:
    execroot/                        <- execution root (where CLI is invoked)
        <project_dir>/               <- project directory (e.g., ".mytool")
            config.json              <- persistent configuration file
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

