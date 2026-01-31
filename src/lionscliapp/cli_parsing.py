"""
cli_parsing: CLI argument ingestion and interpretation (v0).

This module owns argv processing in two phases:

1. ingest_argv(argv)
   Reads argv left-to-right, separating options from positional tokens.
   Options go to cli_state.g or override_inputs.cli_overrides.
   Positional tokens collect into cli_state.positional_args.

2. interpret_arguments()
   Interprets positional_args based on command semantics.
   Built-in commands (set, get, help) have specific argument patterns.
   User commands accept only the command name (no additional positionals).

All values are stored as raw strings. Coercion happens later in ctx building.
"""

from lionscliapp import cli_state
from lionscliapp import override_inputs


def ingest_argv(argv: list[str]) -> None:
    """
    Parse command-line arguments into cli_state and override_inputs.

    Separates options (--key value) from positional tokens.
    Options are handled immediately; positionals are collected for later
    interpretation by interpret_arguments().

    Args:
        argv: Command-line arguments (typically sys.argv[1:])

    Raises:
        ValueError: On malformed input (missing value, short options, etc.)
    """
    cli_state.reset_cli_state()
    override_inputs.cli_overrides.clear()

    i = 0
    while i < len(argv):
        token = argv[i]

        if token.startswith("--"):
            i = _handle_option(argv, i)
        elif token.startswith("-"):
            raise ValueError(f"Short options not supported: '{token}'")
        else:
            cli_state.positional_args.append(token)
            i += 1


def _handle_option(argv: list[str], i: int) -> int:
    """
    Handle a --option value pair starting at index i.

    Returns the next index to process.

    Raises:
        ValueError: If option name is empty or value is missing.
    """
    token = argv[i]
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

    return i + 2


def interpret_arguments() -> None:
    """
    Interpret positional arguments based on command semantics.

    Built-in commands have specific argument patterns:
        set <key> <value>   - requires exactly 2 arguments after command
        get <key>           - requires exactly 1 argument after command
        help [command]      - accepts 0 or 1 argument after command

    User commands accept no additional positional arguments.

    Results are written to cli_state.g:
        command      - the command name (or "" if none provided)
        key          - for set/get commands
        value        - for set command
        command_help - for help command (None if bare "help")

    Raises:
        ValueError: If argument count doesn't match command requirements.
    """
    args = cli_state.positional_args

    if not args:
        cli_state.g["command"] = ""
        return

    command = args[0]
    cli_state.g["command"] = command

    if command == "set":
        _interpret_set(args)
    elif command == "get":
        _interpret_get(args)
    elif command == "help":
        _interpret_help(args)
    else:
        _interpret_user_command(args)


def _interpret_set(args: list[str]) -> None:
    """Interpret 'set <key> <value>' arguments."""
    if len(args) != 3:
        raise ValueError("set command requires exactly 2 arguments: set <key> <value>")
    cli_state.g["key"] = args[1]
    cli_state.g["value"] = args[2]


def _interpret_get(args: list[str]) -> None:
    """Interpret 'get <key>' arguments."""
    if len(args) != 2:
        raise ValueError("get command requires exactly 1 argument: get <key>")
    cli_state.g["key"] = args[1]


def _interpret_help(args: list[str]) -> None:
    """Interpret 'help [command]' arguments."""
    if len(args) > 2:
        raise ValueError("help command accepts at most 1 argument: help [command]")
    if len(args) == 2:
        cli_state.g["command_help"] = args[1]
    # else: command_help remains None (bare "help")


def _interpret_user_command(args: list[str]) -> None:
    """Interpret user command (no additional positional arguments allowed)."""
    if len(args) > 1:
        raise ValueError(
            f"Command '{args[0]}' does not accept positional arguments: '{args[1]}'"
        )
