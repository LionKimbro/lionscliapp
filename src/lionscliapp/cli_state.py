"""
cli_state: Global state for CLI argument parsing results.

This module holds the canonical state populated by cli_parsing.ingest_argv().
Other modules (execroot resolution, override merging, dispatch) read from here.

All values are raw strings as received from argv. Semantic typing (e.g.,
converting paths to pathlib.Path) happens in later phases.

Global state:
    g: Scalar facts (command, options_file, execroot_override)
    option_overrides: Dict of dot-namespaced option overrides
"""

g = {
    "command": None,              # None | str
    "options_file": None,         # None | str (path)
    "execroot_override": None,    # None | str (path)
}

option_overrides = {}  # dict[str, str]


def reset_cli_state():
    """
    Reset all CLI state to initial values.

    Clears g to None values and empties option_overrides.
    Called at the start of ingest_argv() and by app.reset().
    """
    g["command"] = None
    g["options_file"] = None
    g["execroot_override"] = None
    option_overrides.clear()
