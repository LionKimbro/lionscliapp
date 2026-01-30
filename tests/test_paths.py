"""Tests for lionscliapp.paths module."""

import pytest
from pathlib import Path

import lionscliapp as app
from lionscliapp.application import application
from lionscliapp.resolve_execroot import resolve_execroot
from lionscliapp.paths import get_project_root, ensure_project_root_exists


def setup_function():
    """Reset all global state before each test."""
    app.reset()


def test_get_project_root_returns_execroot_joined_with_project_dir(tmp_path):
    """get_project_root() returns execroot / project_dir."""
    application["names"]["project_dir"] = ".myproject"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        result = get_project_root()

        assert result == tmp_path / ".myproject"
        assert isinstance(result, Path)
    finally:
        os.chdir(original_cwd)


def test_get_project_root_raises_when_execroot_not_initialized():
    """get_project_root() raises RuntimeError if execroot not initialized."""
    application["names"]["project_dir"] = ".myproject"

    with pytest.raises(RuntimeError, match="execroot not initialized"):
        get_project_root()


def test_get_project_root_with_dotfile_project_dir(tmp_path):
    """get_project_root() works with dotfile names like '.foo'."""
    application["names"]["project_dir"] = ".foo"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        result = get_project_root()

        assert result == tmp_path / ".foo"
    finally:
        os.chdir(original_cwd)


def test_get_project_root_with_nested_project_dir(tmp_path):
    """get_project_root() works with nested directory names."""
    application["names"]["project_dir"] = "config/app"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        result = get_project_root()

        assert result == tmp_path / "config" / "app"
    finally:
        os.chdir(original_cwd)


def test_get_project_root_with_simple_name(tmp_path):
    """get_project_root() works with simple directory names."""
    application["names"]["project_dir"] = "myapp"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        result = get_project_root()

        assert result == tmp_path / "myapp"
    finally:
        os.chdir(original_cwd)


def test_ensure_project_root_exists_creates_directory(tmp_path):
    """ensure_project_root_exists() creates the directory when missing."""
    application["names"]["project_dir"] = ".myproject"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        project_root = tmp_path / ".myproject"
        assert not project_root.exists()

        result = ensure_project_root_exists()

        assert project_root.exists()
        assert project_root.is_dir()
        assert result == project_root
    finally:
        os.chdir(original_cwd)


def test_ensure_project_root_exists_is_idempotent(tmp_path):
    """ensure_project_root_exists() succeeds when directory already exists."""
    application["names"]["project_dir"] = ".myproject"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        project_root = tmp_path / ".myproject"
        project_root.mkdir()

        result = ensure_project_root_exists()

        assert project_root.exists()
        assert result == project_root
    finally:
        os.chdir(original_cwd)


def test_ensure_project_root_exists_creates_parents(tmp_path):
    """ensure_project_root_exists() creates parent directories for nested paths."""
    application["names"]["project_dir"] = "config/nested/app"

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        project_root = tmp_path / "config" / "nested" / "app"
        assert not project_root.exists()

        result = ensure_project_root_exists()

        assert project_root.exists()
        assert project_root.is_dir()
        assert result == project_root
    finally:
        os.chdir(original_cwd)


def test_ensure_project_root_exists_raises_when_execroot_not_initialized():
    """ensure_project_root_exists() raises RuntimeError if execroot not initialized."""
    application["names"]["project_dir"] = ".myproject"

    with pytest.raises(RuntimeError, match="execroot not initialized"):
        ensure_project_root_exists()
