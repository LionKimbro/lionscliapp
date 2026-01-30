"""Tests for lionscliapp.resolve_execroot module."""

import pytest
from pathlib import Path

import lionscliapp as app
from lionscliapp.application import application
from lionscliapp.execroot import get_execroot
from lionscliapp.cli_state import g as cli_state_g
from lionscliapp.resolve_execroot import resolve_execroot


def setup_function():
    """Reset all global state before each test."""
    app.reset()
    cli_state_g["execroot_override"] = None


def test_resolve_execroot_uses_cwd_by_default():
    """resolve_execroot() uses current working directory when no override."""
    resolve_execroot()

    assert get_execroot() == Path.cwd()


def test_resolve_execroot_uses_cli_override_when_allowed():
    """resolve_execroot() uses CLI override when allow_execroot_override is true."""
    override_path = Path("/some/custom/path")
    cli_state_g["execroot_override"] = override_path

    resolve_execroot()

    assert get_execroot() == override_path


def test_resolve_execroot_raises_when_override_not_allowed():
    """resolve_execroot() raises ValueError when override provided but not allowed."""
    application["flags"]["allow_execroot_override"] = False
    cli_state_g["execroot_override"] = Path("/some/path")

    with pytest.raises(ValueError, match="allow_execroot_override is false"):
        resolve_execroot()


def test_resolve_execroot_ignores_none_override():
    """resolve_execroot() ignores cli_state override when it is None."""
    cli_state_g["execroot_override"] = None

    resolve_execroot()

    assert get_execroot() == Path.cwd()


def test_resolve_execroot_raises_if_called_twice():
    """resolve_execroot() raises RuntimeError if execroot already set."""
    resolve_execroot()

    with pytest.raises(RuntimeError, match="already set"):
        resolve_execroot()


def test_resolve_execroot_searches_upwards_when_enabled(tmp_path):
    """resolve_execroot() searches parent directories when flag is enabled."""
    # Create nested structure: tmp_path/.myproject/  (project dir exists here)
    #                          tmp_path/subdir/deeper/  (cwd will be here)
    project_dir = ".myproject"
    application["names"]["project_dir"] = project_dir
    application["flags"]["search_upwards_for_project_dir"] = True

    # Create the project directory at tmp_path level
    (tmp_path / project_dir).mkdir()

    # Create nested subdirectory
    deeper = tmp_path / "subdir" / "deeper"
    deeper.mkdir(parents=True)

    # Change to the deeper directory
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(deeper)
        resolve_execroot()
        # Should find project dir at tmp_path, not at deeper
        assert get_execroot() == tmp_path
    finally:
        os.chdir(original_cwd)


def test_resolve_execroot_uses_cwd_when_upward_search_finds_nothing(tmp_path):
    """resolve_execroot() uses cwd when upward search finds no project dir."""
    project_dir = ".nonexistent"
    application["names"]["project_dir"] = project_dir
    application["flags"]["search_upwards_for_project_dir"] = True

    # Create a directory with no project dir anywhere above
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(workdir)
        resolve_execroot()
        # Should fall back to cwd since nothing found
        assert get_execroot() == workdir
    finally:
        os.chdir(original_cwd)


def test_resolve_execroot_cli_override_bypasses_upward_search():
    """CLI override takes precedence over upward search."""
    application["flags"]["search_upwards_for_project_dir"] = True
    override_path = Path("/explicit/override")
    cli_state_g["execroot_override"] = override_path

    resolve_execroot()

    # Should use override, not search
    assert get_execroot() == override_path


def test_resolve_execroot_no_search_when_flag_disabled(tmp_path):
    """resolve_execroot() does not search upwards when flag is false."""
    project_dir = ".myproject"
    application["names"]["project_dir"] = project_dir
    application["flags"]["search_upwards_for_project_dir"] = False

    # Create project dir at parent level
    (tmp_path / project_dir).mkdir()

    # Create subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        resolve_execroot()
        # Should NOT find parent's project dir, should use cwd
        assert get_execroot() == subdir
    finally:
        os.chdir(original_cwd)
