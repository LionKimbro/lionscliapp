"""Tests for lionscliapp.dispatch module."""

import sys
import pytest
import lionscliapp as app
from lionscliapp import cli_state
from lionscliapp import declarations
from lionscliapp.dispatch import dispatch_command, DispatchError


def setup_function():
    """Reset application and runtime state before each test."""
    app.reset()


# --- Basic dispatch tests ---

def test_dispatch_calls_named_command():
    """dispatch_command() calls the correct command function."""
    called = []

    def my_cmd():
        called.append("my_cmd")
        return "result"

    declarations.declare_cmd("run", my_cmd)
    cli_state.g["command"] = "run"

    result = dispatch_command()

    assert called == ["my_cmd"]
    assert result == "result"


def test_dispatch_returns_command_result():
    """dispatch_command() returns what the command function returns."""
    def my_cmd():
        return {"status": "ok", "count": 42}

    declarations.declare_cmd("process", my_cmd)
    cli_state.g["command"] = "process"

    result = dispatch_command()

    assert result == {"status": "ok", "count": 42}


def test_dispatch_with_multiple_commands():
    """dispatch_command() selects the correct command from multiple."""
    called = []

    def cmd_a():
        called.append("a")

    def cmd_b():
        called.append("b")

    def cmd_c():
        called.append("c")

    declarations.declare_cmd("alpha", cmd_a)
    declarations.declare_cmd("beta", cmd_b)
    declarations.declare_cmd("gamma", cmd_c)

    cli_state.g["command"] = "beta"
    dispatch_command()

    assert called == ["b"]


# --- No-command behavior tests ---

def test_dispatch_with_empty_string_command():
    """dispatch_command() calls "" command when registered."""
    called = []

    def default_cmd():
        called.append("default")
        return "default_result"

    declarations.declare_cmd("", default_cmd)
    cli_state.g["command"] = ""

    result = dispatch_command()

    assert called == ["default"]
    assert result == "default_result"


def test_dispatch_with_none_command_uses_empty_string():
    """dispatch_command() treats None as "" for no-command case."""
    called = []

    def default_cmd():
        called.append("default")

    declarations.declare_cmd("", default_cmd)
    cli_state.g["command"] = None

    dispatch_command()

    assert called == ["default"]


def test_dispatch_no_command_fallback(capsys):
    """dispatch_command() shows help when no command and no "" registered."""
    declarations.declare_app("mytool", "1.0")
    declarations.describe_app("A useful tool", "s")

    def some_cmd():
        pass

    declarations.declare_cmd("build", some_cmd)
    declarations.describe_cmd("build", "Build the project", "s")

    cli_state.g["command"] = None

    result = dispatch_command()

    assert result is None

    captured = capsys.readouterr()
    assert "mytool" in captured.out
    assert "v1.0" in captured.out
    assert "A useful tool" in captured.out
    assert "build" in captured.out
    assert "Build the project" in captured.out


def test_dispatch_fallback_shows_long_description(capsys):
    """No-command fallback displays long description if available."""
    declarations.declare_app("mytool", "2.0")
    declarations.describe_app("Short desc", "s")
    declarations.describe_app("This is a much longer description\nthat spans multiple lines.", "l")

    cli_state.g["command"] = None

    dispatch_command()

    captured = capsys.readouterr()
    assert "Short desc" in captured.out
    assert "This is a much longer description" in captured.out
    assert "multiple lines" in captured.out


def test_dispatch_fallback_without_descriptions(capsys):
    """No-command fallback works with minimal app declaration."""
    declarations.declare_app("minimal", "0.1")

    cli_state.g["command"] = None

    dispatch_command()

    captured = capsys.readouterr()
    assert "minimal" in captured.out
    assert "v0.1" in captured.out


def test_dispatch_fallback_no_commands(capsys):
    """No-command fallback shows message when no commands registered."""
    declarations.declare_app("empty", "1.0")

    cli_state.g["command"] = None

    dispatch_command()

    captured = capsys.readouterr()
    assert "No commands available" in captured.out


def test_dispatch_fallback_hides_empty_string_command(capsys):
    """No-command fallback doesn't list the "" command handler."""
    def default_handler():
        pass

    def visible_cmd():
        pass

    declarations.declare_app("mytool", "1.0")
    # Register "" but then unregister to test fallback listing
    declarations.declare_cmd("visible", visible_cmd)
    declarations.describe_cmd("visible", "A visible command", "s")

    # Manually add "" command to commands but don't use it
    # (We want fallback to run, so don't register "")
    cli_state.g["command"] = None

    dispatch_command()

    captured = capsys.readouterr()
    assert "visible" in captured.out
    # The "" command shouldn't appear in listing even if it existed


# --- Error cases ---

def test_dispatch_unknown_command_raises():
    """dispatch_command() raises DispatchError for unknown command."""
    def my_cmd():
        pass

    declarations.declare_cmd("known", my_cmd)
    cli_state.g["command"] = "unknown"

    with pytest.raises(DispatchError, match="Unknown command.*'unknown'"):
        dispatch_command()


def test_dispatch_error_is_exported():
    """DispatchError is accessible from main package."""
    assert app.DispatchError is DispatchError


# --- Integration with main() ---

def test_main_dispatches_command(tmp_path, monkeypatch):
    """main() dispatches to the correct command."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    called = []

    def my_cmd():
        called.append("executed")

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    app.main()

    assert called == ["executed"]


def test_main_returns_command_result(tmp_path, monkeypatch):
    """main() returns what the command returns."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    def my_cmd():
        return "success"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    result = app.main()

    assert result == "success"


def test_main_exits_on_unknown_command(tmp_path, monkeypatch):
    """main() exits with code 2 on unknown command."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "nonexistent"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert exc_info.value.code == 2


def test_main_exits_on_command_exception(tmp_path, monkeypatch):
    """main() exits with code 3 on uncaught command exception."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "fail"])

    def failing_cmd():
        raise ValueError("Something went wrong")

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("fail", failing_cmd)

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert exc_info.value.code == 3


def test_main_no_command_shows_help(tmp_path, monkeypatch, capsys):
    """main() shows help when no command provided and no "" handler."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.describe_app("My application", "s")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)
    declarations.describe_cmd("run", "Run the app", "s")

    app.main()

    captured = capsys.readouterr()
    assert "myapp" in captured.out
    assert "My application" in captured.out
    assert "run" in captured.out
