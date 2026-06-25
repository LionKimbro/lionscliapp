"""
entrypoint: Minimal application execution entry point.

This module provides the main() function that transitions the framework
through its lifecycle phases: declaring -> running -> shutdown.

Usage:
    import lionscliapp as app

    app.declare_app("mytool", "1.0")
    app.declare_cmd("run", my_run_fn)
    # ... more declarations ...

    app.main()  # Validates and runs lifecycle

Exit codes (from spec):
    0: Command executed successfully
    1: Validation, configuration, or CLI parsing error
    2: Unknown command or unbound command function
    3: Uncaught exception during command execution
"""

import sys

from lionscliapp import application as appmodel
from lionscliapp import runtime_state
from lionscliapp import resolve_execroot
from lionscliapp import cli_parsing
from lionscliapp import cli_state
from lionscliapp import config_io
from lionscliapp import override_inputs
from lionscliapp import locking
from lionscliapp import tkruntime
from lionscliapp.ctx import build_ctx
from lionscliapp.paths import ensure_project_root_exists
from lionscliapp.dispatch import dispatch_command, DispatchError


class StartupError(Exception):
    """Raised for validation, configuration, or CLI parsing errors."""
    pass


def main():
    """
    Minimal application entry point.

    Validates the application model, ensures all commands have fn bound,
    then transitions through the execution lifecycle:
    declaring -> running -> shutdown

    This implementation:
    - Parses CLI arguments into cli_state
    - Creates project directory if missing
    - Loads raw_config from disk
    - Constructs ctx (merges defaults, config, CLI overrides; coerces by namespace)

    Exit codes:
        0: Command executed successfully (or no command with fallback help)
        1: Validation, configuration, or CLI parsing error
        2: Unknown command
        3: Uncaught exception during command execution
    """
    try:
        _startup()
        tk_action = tkruntime.prepare_current_command(sys.argv[1:])
        if tk_action == "summoned":
            return None
        locking.acquire_lock_for_current_command()
    except (StartupError, locking.LockError, tkruntime.TkRuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = dispatch_command()
        return result
    except DispatchError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    finally:
        try:
            locking.release_lock_for_current_command()
        except locking.LockError as e:
            print(f"Error: {e}", file=sys.stderr)
        try:
            tkruntime.release_instance()
        except tkruntime.TkRuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
        # Transition to shutdown
        runtime_state.transition_to_shutdown()


def _startup():
    """
    Execute all startup steps before command dispatch.

    Validates application, parses CLI, resolves execroot, loads config,
    and builds ctx.

    Raises:
        StartupError: If any startup step fails.
    """
    try:
        # Validate application model
        appmodel.validate_application()

        # Ensure all commands have fn bound
        appmodel.ensure_commands_bound()

        # Ingest CLI arguments
        cli_parsing.ingest_argv(sys.argv[1:])
        cli_parsing.interpret_arguments()

        # Apply --project-dir override if provided (before execroot resolution
        # so that upward search uses the overridden name)
        _apply_project_dir_override_if_requested()

        # Transition to running
        runtime_state.transition_to_running()

        # Resolve execution root
        resolve_execroot.resolve_execroot()

        # Ensure project directory exists
        ensure_project_root_exists()

        # Load raw config (disk -> raw_config)
        config_io.load_config()

        # Load options file (if --options-file specified)
        override_inputs.load_options_file()

        # Build ctx (merge layers, coerce by namespace)
        build_ctx()

    except (ValueError, RuntimeError, OSError) as e:
        raise StartupError(str(e)) from e


def _apply_project_dir_override_if_requested():
    """
    Apply --project-dir override to application["names"]["project_dir"] in place.

    Called after argv is parsed, before execroot resolution, so that the
    upward search (search_upwards_for_project_dir) uses the overridden name.

    Raises:
        ValueError: If override is not allowed, empty, or contains path separators.
    """
    override = cli_state.g["project_dir_override"]
    if override is None:
        return

    if not appmodel.application["flags"]["allow_projectdir_override"]:
        raise ValueError(
            "--project-dir override provided but allow_projectdir_override is false"
        )

    if not override:
        raise ValueError("--project-dir: value must not be empty")

    if "/" in override or "\\" in override:
        raise ValueError(
            f"--project-dir: value must be a directory name, not a path "
            f"(no slashes allowed): {override!r}"
        )

    appmodel.application["names"]["project_dir"] = override
