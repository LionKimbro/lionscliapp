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


# --- Validation tests ---

def test_main_raises_on_invalid_application():
    """main() raises ValueError if application is invalid."""
    # Application not properly set up (missing required fields)
    appmodel.application.clear()
    appmodel.application["id"] = {}  # Invalid: missing required fields

    with pytest.raises((ValueError, RuntimeError)):
        main()


def test_main_raises_on_unbound_command():
    """main() raises RuntimeError if a command has fn=None."""
    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.describe_cmd("run", "A command without fn bound")
    # Note: describe_cmd creates command but leaves fn=None

    with pytest.raises(RuntimeError, match="unbound fn"):
        main()


def test_main_raises_on_multiple_unbound_commands():
    """main() error message includes all unbound command names."""
    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.describe_cmd("build", "Build command")
    declarations.describe_cmd("deploy", "Deploy command")

    with pytest.raises(RuntimeError, match="'build'.*'deploy'|'deploy'.*'build'"):
        main()


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
