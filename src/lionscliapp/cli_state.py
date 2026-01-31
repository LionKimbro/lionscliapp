"""
cli_state: Global state for CLI argument parsing results.

This module holds the canonical state populated by cli_parsing.
Other modules (execroot resolution, override merging, dispatch) read from here.

All values are raw strings as received from argv. Semantic typing (e.g.,
converting paths to pathlib.Path) happens in later phases.

Global state:
    g: Scalar facts parsed from CLI
    positional_args: Positional tokens collected during ingestion

Parsing is two-phase:
    1. ingest_argv() populates positional_args and option-related keys in g
    2. interpret_arguments() interprets positional_args into command-specific keys

Note: Option overrides (--key value) are written directly to
override_inputs.cli_overrides by cli_parsing.
"""

g = {
    # Set by ingest_argv
    "options_file": None,         # None | str (path)
    "execroot_override": None,    # None | str (path)

    # Set by interpret_arguments
    "command": None,              # None | str
    "key": None,                  # None | str (for set/get commands)
    "value": None,                # None | str (for set command)
    "command_help": None,         # None | str (for help command)
}

positional_args = []


def reset_cli_state():
    """
    Reset all CLI state to initial values.

    Clears g to None values and empties positional_args.
    Called at the start of ingest_argv() and by app.reset().
    """
    g["options_file"] = None
    g["execroot_override"] = None
    g["command"] = None
    g["key"] = None
    g["value"] = None
    g["command_help"] = None
    del positional_args[:]
