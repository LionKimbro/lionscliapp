"""Tests for lionscliapp.entrypoint module."""

import sys
import pytest
import lionscliapp as app
from lionscliapp import application as appmodel
from lionscliapp import runtime_state
from lionscliapp import declarations
from lionscliapp.entrypoint import main


def setup_function():
    """Reset application and runtime state before each test."""
    app.reset()


# --- Phase transition tests ---

def test_main_transitions_to_shutdown(tmp_path, monkeypatch):
    """main() transitions phase from declaring through running to shutdown."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    assert runtime_state.get_phase() == "declaring"

    main()

    assert runtime_state.get_phase() == "shutdown"


def test_main_passes_through_running_phase(tmp_path, monkeypatch):
    """main() transitions through running phase before shutdown."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp"])
    phases_seen = []

    def capture_phase():
        phases_seen.append(runtime_state.get_phase())

    # Patch transition_to_shutdown to capture the phase before it changes
    original_shutdown = runtime_state.transition_to_shutdown

    def patched_shutdown():
        phases_seen.append(runtime_state.get_phase())
        original_shutdown()

    runtime_state.transition_to_shutdown = patched_shutdown

    try:
        declarations.declare_app("myapp", "1.0")
        declarations.declare_projectdir(".myapp")
        declarations.declare_cmd("run", capture_phase)
        main()
    finally:
        runtime_state.transition_to_shutdown = original_shutdown

    assert "running" in phases_seen


# --- Mutation blocking tests ---

def test_declarations_blocked_after_main(tmp_path, monkeypatch):
    """Declarations are blocked after main() completes (shutdown phase)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    main()

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare_app("another", "2.0")


# --- Exit code 1: Validation, configuration, CLI parsing errors ---

def test_main_exits_code_1_on_invalid_application():
    """main() exits with code 1 if application is invalid."""
    # Application not properly set up (missing required fields)
    appmodel.application.clear()
    appmodel.application["id"] = {}  # Invalid: missing required fields

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_exits_code_1_on_unbound_command():
    """main() exits with code 1 if a command has fn=None."""
    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.describe_cmd("run", "A command without fn bound")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_exits_code_1_on_cli_parsing_error(monkeypatch):
    """main() exits with code 1 on CLI parsing error."""
    monkeypatch.setattr(sys, "argv", ["myapp", "--missing-value"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_exits_code_1_on_invalid_config(tmp_path, monkeypatch):
    """main() exits with code 1 if config.json is invalid."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    # Create invalid config file
    project_dir = tmp_path / ".myapp"
    project_dir.mkdir()
    config_path = project_dir / "config.json"
    config_path.write_text("not valid json")

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_exits_code_1_on_invalid_options_file(tmp_path, monkeypatch):
    """main() exits with code 1 if --options-file contains invalid JSON."""
    monkeypatch.chdir(tmp_path)

    # Create invalid options file
    opts_file = tmp_path / "opts.json"
    opts_file.write_text("{invalid json}")

    monkeypatch.setattr(sys, "argv", ["myapp", "--options-file", str(opts_file), "run"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_exits_code_1_on_coercion_error(tmp_path, monkeypatch):
    """main() exits with code 1 if value coercion fails."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "--json.indent.foo", "not-a-number", "run"])

    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("json.indent.foo", 2)
    declarations.declare_cmd("run", my_cmd)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_startup_error_is_exported():
    """StartupError is accessible from main package."""
    from lionscliapp.entrypoint import StartupError
    assert app.StartupError is StartupError


# --- ensure_commands_bound tests ---

def test_ensure_commands_bound_passes_with_all_bound():
    """ensure_commands_bound() passes when all commands have fn."""
    def my_cmd():
        pass

    declarations.declare_cmd("run", my_cmd)

    appmodel.ensure_commands_bound()  # Should not raise


def test_ensure_commands_bound_passes_with_no_commands():
    """ensure_commands_bound() passes when there are no commands."""
    appmodel.ensure_commands_bound()  # Should not raise


def test_ensure_commands_bound_raises_on_unbound():
    """ensure_commands_bound() raises for unbound commands."""
    declarations.describe_cmd("run", "A command")

    with pytest.raises(RuntimeError, match="unbound fn"):
        appmodel.ensure_commands_bound()
