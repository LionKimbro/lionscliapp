"""Tests for lionscliapp.config_io module."""

import json
import os
import pytest

import lionscliapp as app
from lionscliapp.application import application
from lionscliapp.resolve_execroot import resolve_execroot
from lionscliapp.config_io import raw_config, load_config, write_config, reset_config
from lionscliapp.paths import get_config_path


def setup_function():
    """Reset all global state before each test."""
    app.reset()


def test_load_config_missing_file_returns_minimal_config(tmp_path):
    """load_config() with missing file sets raw_config to {"options": {}}."""
    application["names"]["project_dir"] = ".myproject"

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        load_config()

        assert raw_config == {"options": {}}
    finally:
        os.chdir(original_cwd)


def test_load_config_missing_file_does_not_create_file(tmp_path):
    """load_config() with missing file does not write to disk."""
    application["names"]["project_dir"] = ".myproject"

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        load_config()

        config_path = get_config_path()
        assert not config_path.exists()
    finally:
        os.chdir(original_cwd)


def test_load_config_invalid_json_raises(tmp_path):
    """load_config() raises JSONDecodeError for invalid JSON."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text("{ invalid json }", encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        with pytest.raises(json.JSONDecodeError):
            load_config()
    finally:
        os.chdir(original_cwd)


def test_load_config_non_dict_raises(tmp_path):
    """load_config() raises RuntimeError if config is not a dict."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('["a", "list"]', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        with pytest.raises(RuntimeError, match="must contain a JSON object"):
            load_config()
    finally:
        os.chdir(original_cwd)


def test_load_config_missing_options_key_adds_it(tmp_path):
    """load_config() adds {"options": {}} if key is missing."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"foo": "bar"}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        load_config()

        assert raw_config == {"foo": "bar", "options": {}}
    finally:
        os.chdir(original_cwd)


def test_load_config_preserves_existing_options(tmp_path):
    """load_config() preserves existing options key."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"key": "value"}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        load_config()

        assert raw_config == {"options": {"key": "value"}}
    finally:
        os.chdir(original_cwd)


def test_load_config_updates_raw_config_global(tmp_path):
    """load_config() updates the raw_config global in place."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"a": 1}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        # Set something in raw_config first
        raw_config["stale"] = "data"

        load_config()

        # Old data should be cleared
        assert "stale" not in raw_config
        assert raw_config == {"options": {"a": 1}}
    finally:
        os.chdir(original_cwd)


def test_write_config_creates_file(tmp_path):
    """write_config() creates config.json on disk."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        raw_config.clear()
        raw_config["options"] = {"key": "value"}

        write_config()

        config_path = get_config_path()
        assert config_path.exists()
        content = json.loads(config_path.read_text(encoding="utf-8"))
        assert content == {"options": {"key": "value"}}
    finally:
        os.chdir(original_cwd)


def test_write_config_uses_correct_formatting(tmp_path):
    """write_config() uses indent=2, sort_keys=True, trailing newline."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        raw_config.clear()
        raw_config["z"] = 1
        raw_config["a"] = 2
        raw_config["options"] = {}

        write_config()

        config_path = get_config_path()
        text = config_path.read_text(encoding="utf-8")

        # Should be sorted and indented
        assert text.startswith('{\n  "a"')
        assert text.endswith("}\n")
    finally:
        os.chdir(original_cwd)


def test_write_config_creates_parent_directories(tmp_path):
    """write_config() creates project directory if it doesn't exist."""
    application["names"]["project_dir"] = ".myproject"

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        raw_config.clear()
        raw_config["options"] = {}

        write_config()

        config_path = get_config_path()
        assert config_path.exists()
    finally:
        os.chdir(original_cwd)


def test_write_then_load_roundtrip(tmp_path):
    """write_config() followed by load_config() preserves data."""
    application["names"]["project_dir"] = ".myproject"
    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()

        raw_config.clear()
        raw_config["options"] = {"nested": {"key": [1, 2, 3]}}
        raw_config["meta"] = "test"

        write_config()

        # Clear and reload
        raw_config.clear()
        load_config()

        assert raw_config == {"options": {"nested": {"key": [1, 2, 3]}}, "meta": "test"}
    finally:
        os.chdir(original_cwd)


def test_reset_config_clears_raw_config():
    """reset_config() clears raw_config."""
    raw_config["foo"] = "bar"
    raw_config["options"] = {"key": "value"}

    reset_config()

    assert raw_config == {}
