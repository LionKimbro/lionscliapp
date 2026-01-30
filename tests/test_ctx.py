"""Tests for lionscliapp.ctx module."""

import os
from pathlib import Path

import pytest

import lionscliapp as app
from lionscliapp.application import application
from lionscliapp.resolve_execroot import resolve_execroot
from lionscliapp.config_io import raw_config, load_config
from lionscliapp import cli_state
from lionscliapp.ctx import ctx, build_ctx, reset_ctx


def setup_function():
    """Reset all global state before each test."""
    app.reset()


# =============================================================================
# Layer merging tests
# =============================================================================

def test_build_ctx_defaults_only(tmp_path):
    """build_ctx() uses declared defaults when no config or CLI overrides."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["db.host"] = {"default": "localhost", "short": None, "long": None}
    application["options"]["db.port"] = {"default": 5432, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["db.host"] == "localhost"
        assert ctx["db.port"] == 5432
    finally:
        os.chdir(original_cwd)


def test_build_ctx_config_overrides_defaults(tmp_path):
    """build_ctx() uses config values over defaults."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["db.host"] = {"default": "localhost", "short": None, "long": None}
    application["options"]["db.port"] = {"default": 5432, "short": None, "long": None}

    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"db.host": "remotehost"}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["db.host"] == "remotehost"  # from config
        assert ctx["db.port"] == 5432  # from default
    finally:
        os.chdir(original_cwd)


def test_build_ctx_cli_overrides_config(tmp_path):
    """build_ctx() uses CLI overrides over config values."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["db.host"] = {"default": "localhost", "short": None, "long": None}

    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"db.host": "confighost"}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        cli_state.option_overrides["db.host"] = "clihost"

        build_ctx()

        assert ctx["db.host"] == "clihost"
    finally:
        os.chdir(original_cwd)


def test_build_ctx_cli_overrides_defaults(tmp_path):
    """build_ctx() uses CLI overrides over defaults (no config)."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["db.host"] = {"default": "localhost", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        cli_state.option_overrides["db.host"] = "clihost"

        build_ctx()

        assert ctx["db.host"] == "clihost"
    finally:
        os.chdir(original_cwd)


def test_build_ctx_full_layering(tmp_path):
    """build_ctx() correctly layers defaults < config < CLI."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["a"] = {"default": "default_a", "short": None, "long": None}
    application["options"]["b"] = {"default": "default_b", "short": None, "long": None}
    application["options"]["c"] = {"default": "default_c", "short": None, "long": None}

    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"b": "config_b", "c": "config_c"}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        cli_state.option_overrides["c"] = "cli_c"

        build_ctx()

        assert ctx["a"] == "default_a"  # only default
        assert ctx["b"] == "config_b"   # config overrode default
        assert ctx["c"] == "cli_c"      # CLI overrode config
    finally:
        os.chdir(original_cwd)


def test_build_ctx_ignores_undeclared_keys_in_config(tmp_path):
    """build_ctx() ignores config keys not declared in application.options."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["declared"] = {"default": "default_value", "short": None, "long": None}

    project_dir = tmp_path / ".myproject"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"declared": "config_value", "undeclared": "ignored"}}', encoding="utf-8")

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["declared"] == "config_value"
        assert "undeclared" not in ctx
    finally:
        os.chdir(original_cwd)


def test_build_ctx_ignores_undeclared_keys_in_cli(tmp_path):
    """build_ctx() ignores CLI override keys not declared in application.options."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["declared"] = {"default": "default_value", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        cli_state.option_overrides["declared"] = "cli_value"
        cli_state.option_overrides["undeclared"] = "ignored"

        build_ctx()

        assert ctx["declared"] == "cli_value"
        assert "undeclared" not in ctx
    finally:
        os.chdir(original_cwd)


# =============================================================================
# Path namespace coercion tests
# =============================================================================

def test_coerce_path_absolute(tmp_path):
    """path.* keys are coerced to pathlib.Path (absolute paths unchanged)."""
    application["names"]["project_dir"] = ".myproject"
    # Use tmp_path to construct a truly absolute path that works cross-platform
    absolute_path = str(tmp_path / "absolute" / "path")
    application["options"]["path.output"] = {"default": absolute_path, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert isinstance(ctx["path.output"], Path)
        assert ctx["path.output"] == Path(absolute_path)
    finally:
        os.chdir(original_cwd)


def test_coerce_path_relative_resolved_against_execroot(tmp_path):
    """path.* relative paths are resolved against execroot, not CWD."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["path.output"] = {"default": "relative/path", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert isinstance(ctx["path.output"], Path)
        assert ctx["path.output"] == tmp_path / "relative" / "path"
    finally:
        os.chdir(original_cwd)


def test_coerce_path_expanduser(tmp_path):
    """path.* keys expand ~ to user home directory."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["path.config"] = {"default": "~/myconfig", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert isinstance(ctx["path.config"], Path)
        # After expanduser, should not contain ~
        assert "~" not in str(ctx["path.config"])
        # Should be absolute (expanduser makes it absolute)
        assert ctx["path.config"].is_absolute()
    finally:
        os.chdir(original_cwd)


def test_coerce_path_non_string_raises(tmp_path):
    """path.* raises ValueError if value is not a string."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["path.output"] = {"default": 123, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        with pytest.raises(ValueError, match="path value must be a string"):
            build_ctx()
    finally:
        os.chdir(original_cwd)


def test_coerce_path_deep_namespace(tmp_path):
    """path.* coercion works for deeply nested keys like path.output.inventory."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["path.output.inventory"] = {"default": "output/inv.json", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert isinstance(ctx["path.output.inventory"], Path)
        assert ctx["path.output.inventory"] == tmp_path / "output" / "inv.json"
    finally:
        os.chdir(original_cwd)


# =============================================================================
# json.rendering namespace coercion tests
# =============================================================================

def test_coerce_json_rendering_pretty(tmp_path):
    """json.rendering.* accepts 'pretty'."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.rendering.output"] = {"default": "pretty", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["json.rendering.output"] == "pretty"
    finally:
        os.chdir(original_cwd)


def test_coerce_json_rendering_compact(tmp_path):
    """json.rendering.* accepts 'compact'."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.rendering.output"] = {"default": "compact", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["json.rendering.output"] == "compact"
    finally:
        os.chdir(original_cwd)


def test_coerce_json_rendering_invalid_raises(tmp_path):
    """json.rendering.* raises ValueError for invalid values."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.rendering.output"] = {"default": "invalid", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        with pytest.raises(ValueError, match="must be one of"):
            build_ctx()
    finally:
        os.chdir(original_cwd)


# =============================================================================
# json.indent namespace coercion tests
# =============================================================================

def test_coerce_json_indent_integer(tmp_path):
    """json.indent.* coerces to int."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.indent.output"] = {"default": 4, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["json.indent.output"] == 4
        assert isinstance(ctx["json.indent.output"], int)
    finally:
        os.chdir(original_cwd)


def test_coerce_json_indent_string_to_int(tmp_path):
    """json.indent.* coerces string to int."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.indent.output"] = {"default": "2", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["json.indent.output"] == 2
        assert isinstance(ctx["json.indent.output"], int)
    finally:
        os.chdir(original_cwd)


def test_coerce_json_indent_zero_allowed(tmp_path):
    """json.indent.* allows zero."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.indent.output"] = {"default": 0, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["json.indent.output"] == 0
    finally:
        os.chdir(original_cwd)


def test_coerce_json_indent_negative_raises(tmp_path):
    """json.indent.* raises ValueError for negative values."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.indent.output"] = {"default": -1, "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        with pytest.raises(ValueError, match="must be >= 0"):
            build_ctx()
    finally:
        os.chdir(original_cwd)


def test_coerce_json_indent_non_numeric_raises(tmp_path):
    """json.indent.* raises ValueError for non-numeric values."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["json.indent.output"] = {"default": "abc", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        with pytest.raises(ValueError, match="must be an integer"):
            build_ctx()
    finally:
        os.chdir(original_cwd)


# =============================================================================
# Unknown namespace tests
# =============================================================================

def test_coerce_unknown_namespace_identity(tmp_path):
    """Unknown namespace keys pass through without coercion."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["custom.setting"] = {"default": "value", "short": None, "long": None}
    application["options"]["custom.number"] = {"default": 42, "short": None, "long": None}
    application["options"]["custom.list"] = {"default": [1, 2, 3], "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["custom.setting"] == "value"
        assert ctx["custom.number"] == 42
        assert ctx["custom.list"] == [1, 2, 3]
    finally:
        os.chdir(original_cwd)


def test_coerce_no_namespace_key_identity(tmp_path):
    """Keys without dots pass through without coercion."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["simple"] = {"default": "value", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert ctx["simple"] == "value"
    finally:
        os.chdir(original_cwd)


# =============================================================================
# Reset and mutation tests
# =============================================================================

def test_reset_ctx_clears_ctx():
    """reset_ctx() clears the ctx dict."""
    ctx["foo"] = "bar"
    ctx["baz"] = 123

    reset_ctx()

    assert ctx == {}


def test_build_ctx_clears_previous_ctx(tmp_path):
    """build_ctx() clears any previous ctx contents."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["new.key"] = {"default": "new_value", "short": None, "long": None}

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        ctx["stale.key"] = "stale_value"

        build_ctx()

        assert "stale.key" not in ctx
        assert ctx["new.key"] == "new_value"
    finally:
        os.chdir(original_cwd)


def test_ctx_is_same_object_after_build(tmp_path):
    """build_ctx() modifies ctx in place, not replacing it."""
    application["names"]["project_dir"] = ".myproject"
    application["options"]["key"] = {"default": "value", "short": None, "long": None}

    original_ctx_id = id(ctx)

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        resolve_execroot()
        load_config()

        build_ctx()

        assert id(ctx) == original_ctx_id
    finally:
        os.chdir(original_cwd)
