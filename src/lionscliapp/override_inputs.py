"""
override_inputs: Transient override sources collected before ctx construction.

This module holds all configuration override layers that are applied during
startup before ctx is finalized. These are transient (not written to disk)
and exist only for the duration of app.main().

Override layers (applied in this order during ctx construction):
    cli_overrides           - from CLI --key value arguments
    options_file_overrides  - from --options-file JSON file
    programmatic_overrides  - from app.run() (future)

The merge order in ctx is:
    defaults < raw_config < options_file_overrides < cli_overrides < programmatic_overrides
"""

import json
from pathlib import Path

from lionscliapp import cli_state
from lionscliapp import execroot


cli_overrides = {}            # dict[str, str] from CLI parsing
options_file_overrides = {}   # dict[str, any] from --options-file
programmatic_overrides = {}   # dict[str, any] from app.run() (future)


def load_options_file():
    """
    Load the options file and populate options_file_overrides.

    Reads the path from cli_state.g["options_file"].
    Resolves relative paths against execroot.get_execroot().

    If no options file was specified, clears options_file_overrides and returns.

    Raises:
        FileNotFoundError: If the specified path does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        RuntimeError: If the file does not contain a JSON object.
    """
    options_file_overrides.clear()

    options_file_path = cli_state.g["options_file"]
    if options_file_path is None:
        return

    path = Path(options_file_path).expanduser()
    if not path.is_absolute():
        path = execroot.get_execroot() / path

    if not path.exists():
        raise FileNotFoundError(
            f"Options file not found: {path}"
        )

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in options file: {path}",
            e.doc,
            e.pos
        )

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Options file must contain a JSON object, got {type(data).__name__}: {path}"
        )

    # Extract the "options" key if present
    options = data.get("options", {})
    options_file_overrides.update(options)


def reset_override_inputs():
    """
    Reset all override inputs to empty state.

    Called by app.reset() for tests.
    """
    cli_overrides.clear()
    options_file_overrides.clear()
    programmatic_overrides.clear()
