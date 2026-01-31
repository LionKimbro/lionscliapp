"""Tests for lionscliapp.builtins module."""

import sys
import json
import pytest

import lionscliapp as app
from lionscliapp import cli_state
from lionscliapp import config_io
from lionscliapp import declarations
from lionscliapp.ctx import ctx
from lionscliapp.builtins import (
    is_builtin,
    run_builtin,
    cmd_set,
    cmd_get,
    cmd_help,
    BUILTIN_COMMANDS,
)


def setup_function():
    """Reset all state before each test."""
    app.reset()


# =============================================================================
# is_builtin tests
# =============================================================================

def test_is_builtin_set():
    assert is_builtin("set") is True


def test_is_builtin_get():
    assert is_builtin("get") is True


def test_is_builtin_help():
    assert is_builtin("help") is True


def test_is_builtin_unknown():
    assert is_builtin("build") is False
    assert is_builtin("run") is False
    assert is_builtin("") is False


def test_builtin_commands_constant():
    assert BUILTIN_COMMANDS == {"set", "get", "help"}


# =============================================================================
# set command tests
# =============================================================================

def test_cmd_set_basic(tmp_path, monkeypatch, capsys):
    """set command stores value in config and ctx."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "default_value")

    # Simulate startup
    _simulate_startup(tmp_path)

    # Set up CLI state for set command
    cli_state.g["key"] = "myopt"
    cli_state.g["value"] = "new_value"

    cmd_set()

    # Check ctx updated
    assert ctx["myopt"] == "new_value"

    # Check config file written
    config_path = tmp_path / ".myapp" / "config.json"
    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert data["options"]["myopt"] == "new_value"

    # Check output
    captured = capsys.readouterr()
    assert "Set myopt" in captured.out
    assert "new_value" in captured.out


def test_cmd_set_path_coercion(tmp_path, monkeypatch):
    """set command coerces path values."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.output", "/default")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "path.output"
    cli_state.g["value"] = "relative/path"

    cmd_set()

    # Path should be coerced and resolved against execroot
    from pathlib import Path
    assert isinstance(ctx["path.output"], Path)
    assert ctx["path.output"] == tmp_path / "relative/path"


def test_cmd_set_unknown_key(tmp_path, monkeypatch, capsys):
    """set command rejects unknown keys."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("known.key", "default")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "unknown.key"
    cli_state.g["value"] = "value"

    with pytest.raises(ValueError, match="Unknown option key"):
        cmd_set()

    captured = capsys.readouterr()
    assert "Unknown option" in captured.out
    assert "unknown.key" in captured.out


# =============================================================================
# get command tests
# =============================================================================

def test_cmd_get_shows_default(tmp_path, monkeypatch, capsys):
    """get command shows default value."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "the_default")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "myopt"

    cmd_get()

    captured = capsys.readouterr()
    assert "myopt:" in captured.out
    assert "default:" in captured.out
    assert "the_default" in captured.out


def test_cmd_get_shows_config_value(tmp_path, monkeypatch, capsys):
    """get command shows config file value when set."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "default")

    # Pre-create config with a value
    project_dir = tmp_path / ".myapp"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text('{"options": {"myopt": "from_config"}}')

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "myopt"

    cmd_get()

    captured = capsys.readouterr()
    assert "config:" in captured.out
    assert "from_config" in captured.out


def test_cmd_get_shows_not_set(tmp_path, monkeypatch, capsys):
    """get command shows (not set) when no config value."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "default")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "myopt"

    cmd_get()

    captured = capsys.readouterr()
    assert "(not set)" in captured.out


def test_cmd_get_shows_current_coerced(tmp_path, monkeypatch, capsys):
    """get command shows current coerced value."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.output", "relative")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "path.output"

    cmd_get()

    captured = capsys.readouterr()
    assert "current:" in captured.out
    # Path should show as resolved absolute path (check with forward slashes for cross-platform)
    assert "relative" in captured.out
    assert tmp_path.name in captured.out


def test_cmd_get_unknown_key(tmp_path, monkeypatch, capsys):
    """get command rejects unknown keys."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    cli_state.g["key"] = "nonexistent"

    with pytest.raises(ValueError, match="Unknown option key"):
        cmd_get()


# =============================================================================
# help command tests
# =============================================================================

def test_cmd_help_general(tmp_path, monkeypatch, capsys):
    """help command shows general help."""
    monkeypatch.chdir(tmp_path)

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.describe_app("A test application", "s")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("build", my_cmd)
    declarations.describe_cmd("build", "Build the project", "s")
    declarations.declare_key("path.output", "/tmp")
    declarations.describe_key("path.output", "Output path", "s")

    _simulate_startup(tmp_path)

    cli_state.g["command_help"] = None

    cmd_help()

    captured = capsys.readouterr()
    # App info
    assert "myapp" in captured.out
    assert "A test application" in captured.out
    # Built-in commands
    assert "set" in captured.out
    assert "get" in captured.out
    assert "help" in captured.out
    # User command
    assert "build" in captured.out
    assert "Build the project" in captured.out
    # Options
    assert "path.output" in captured.out
    assert "Output path" in captured.out


def test_cmd_help_builtin_set(tmp_path, monkeypatch, capsys):
    """help set shows set command help."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    cli_state.g["command_help"] = "set"

    cmd_help()

    captured = capsys.readouterr()
    assert "set <key> <value>" in captured.out
    assert "Persist" in captured.out


def test_cmd_help_builtin_get(tmp_path, monkeypatch, capsys):
    """help get shows get command help."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    cli_state.g["command_help"] = "get"

    cmd_help()

    captured = capsys.readouterr()
    assert "get <key>" in captured.out
    assert "Display" in captured.out


def test_cmd_help_user_command(tmp_path, monkeypatch, capsys):
    """help <user-command> shows user command help."""
    monkeypatch.chdir(tmp_path)

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("build", my_cmd)
    declarations.describe_cmd("build", "Short description", "s")
    declarations.describe_cmd("build", "This is a longer description\nwith multiple lines.", "l")

    _simulate_startup(tmp_path)

    cli_state.g["command_help"] = "build"

    cmd_help()

    captured = capsys.readouterr()
    assert "build" in captured.out
    assert "Short description" in captured.out
    assert "longer description" in captured.out


def test_cmd_help_unknown_command(tmp_path, monkeypatch, capsys):
    """help <unknown> shows error."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    cli_state.g["command_help"] = "nonexistent"

    cmd_help()

    captured = capsys.readouterr()
    assert "Unknown command" in captured.out
    assert "nonexistent" in captured.out


# =============================================================================
# Integration tests via main()
# =============================================================================

def test_main_set_command(tmp_path, monkeypatch, capsys):
    """main() dispatches to set command."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "set", "myopt", "myvalue"])

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "default")

    app.main()

    assert ctx["myopt"] == "myvalue"


def test_main_get_command(tmp_path, monkeypatch, capsys):
    """main() dispatches to get command."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "get", "myopt"])

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("myopt", "the_default")

    app.main()

    captured = capsys.readouterr()
    assert "myopt:" in captured.out
    assert "the_default" in captured.out


def test_main_help_command(tmp_path, monkeypatch, capsys):
    """main() dispatches to help command."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "help"])

    declarations.declare_app("myapp", "1.0")
    declarations.describe_app("My application", "s")
    declarations.declare_projectdir(".myapp")

    app.main()

    captured = capsys.readouterr()
    assert "myapp" in captured.out
    assert "My application" in captured.out
    assert "set" in captured.out
    assert "get" in captured.out


def test_main_help_specific_command(tmp_path, monkeypatch, capsys):
    """main() dispatches to help <command>."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "help", "set"])

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    app.main()

    captured = capsys.readouterr()
    assert "set <key> <value>" in captured.out


def test_builtin_takes_precedence_over_user_command(tmp_path, monkeypatch, capsys):
    """Built-in commands cannot be shadowed by user commands."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "help"])

    user_help_called = []

    def user_help():
        user_help_called.append(True)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("help", user_help)  # Try to shadow built-in

    app.main()

    # Built-in should run, not user command
    assert user_help_called == []
    captured = capsys.readouterr()
    assert "Built-in commands:" in captured.out


# =============================================================================
# Helpers
# =============================================================================

def _simulate_startup(tmp_path):
    """
    Simulate the startup sequence that main() would do.

    This sets up execroot, project directory, config, and ctx
    so that built-in commands can be tested in isolation.
    """
    from lionscliapp import runtime_state
    from lionscliapp import execroot
    from lionscliapp.paths import ensure_project_root_exists
    from lionscliapp.ctx import build_ctx

    runtime_state.transition_to_running()
    execroot.set_execroot(tmp_path)
    ensure_project_root_exists()
    config_io.load_config()
    build_ctx()
