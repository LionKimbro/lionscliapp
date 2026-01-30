# cli_parsing.py
"""
CLI argument ingestion layer (v0).

This module owns argv ingestion. It reads argv and writes
parsed results into cli_state and override_inputs. It does not return
anything and does not perform semantic interpretation.

All values are stored as raw strings. No coercion, no typing.
"""

from lionscliapp import cli_state
from lionscliapp import override_inputs


def ingest_argv(argv: list[str]) -> None:
    """
    Parse command-line arguments and populate cli_state and override_inputs.

    Reads argv left-to-right, writing results into:
    - cli_state.g["command"]
    - cli_state.g["execroot_override"]
    - cli_state.g["options_file"]
    - override_inputs.cli_overrides

    Args:
        argv: List of command-line arguments (typically sys.argv[1:])

    Raises:
        ValueError: If argv contains malformed input (missing value,
                    unknown syntax, multiple positional tokens, etc.)
    """
    cli_state.reset_cli_state()
    override_inputs.cli_overrides.clear()

    i = 0
    command_seen = False

    while i < len(argv):
        token = argv[i]

        if token.startswith("--"):
            # Option: must have a following value
            key = token[2:]

            if not key:
                raise ValueError("Empty option name: '--' is not valid")

            if i + 1 >= len(argv):
                raise ValueError(f"Option '{token}' requires a value")

            value = argv[i + 1]

            if key == "execroot":
                cli_state.g["execroot_override"] = value
            elif key == "options-file":
                cli_state.g["options_file"] = value
            else:
                override_inputs.cli_overrides[key] = value

            i += 2

        elif token.startswith("-"):
            # Short options are not supported in v0
            raise ValueError(f"Short options not supported: '{token}'")

        else:
            # Positional token: must be the command
            if command_seen:
                raise ValueError(
                    f"Multiple positional arguments not supported: '{token}'"
                )
            cli_state.g["command"] = token
            command_seen = True
            i += 1
