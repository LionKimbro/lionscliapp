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
"""

import sys

from lionscliapp import application as appmodel
from lionscliapp import runtime_state
from lionscliapp import resolve_execroot
from lionscliapp import cli_parsing
from lionscliapp import config_io
from lionscliapp.ctx import build_ctx
from lionscliapp.paths import ensure_project_root_exists


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

    Raises:
        ValueError: If application validation fails.
        RuntimeError: If application not initialized, commands have unbound fn,
                      or phase transitions fail.
    """
    # Validate application model
    appmodel.validate_application()

    # Ensure all commands have fn bound
    appmodel.ensure_commands_bound()

    # Ingest CLI arguments
    cli_parsing.ingest_argv(sys.argv[1:])
    
    # Transition to running
    runtime_state.transition_to_running()

    # Resolve execution root
    resolve_execroot.resolve_execroot()

    # Ensure project directory exists
    ensure_project_root_exists()

    # Load raw config (disk -> raw_config)
    config_io.load_config()

    # Build ctx (merge layers, coerce by namespace)
    build_ctx()

    try:
        # No actual execution in this minimal version
        pass
    finally:
        # Transition to shutdown
        runtime_state.transition_to_shutdown()
