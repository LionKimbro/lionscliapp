"""
dispatch: Command dispatch logic.

This module resolves the command name from CLI state and invokes the
corresponding command function.

Command resolution rules:
    - If command is None or "", look for a registered "" command
    - If no "" command registered, execute no-command fallback (help display)
    - Otherwise, look up command in application["commands"]
    - Unknown commands raise DispatchError

Exit codes (from spec):
    - 0: Command executed successfully
    - 2: Unknown command or unbound command function
    - 3: Uncaught exception during command execution
"""

from lionscliapp import application as appmodel
from lionscliapp import cli_state


class DispatchError(Exception):
    """Raised when command dispatch fails (unknown command, etc.)."""
    pass


def dispatch_command():
    """
    Dispatch to the appropriate command function.

    Resolves the command from cli_state, looks it up in application["commands"],
    and calls the bound function.

    Returns:
        Whatever the command function returns.

    Raises:
        DispatchError: If command is unknown.
    """
    command = cli_state.g["command"]

    # Normalize None to "" for no-command case
    if command is None:
        command = ""

    commands = appmodel.application["commands"]

    # Check if command exists
    if command in commands:
        fn = commands[command]["fn"]
        return fn()

    # No-command case: if "" not registered, use fallback
    if command == "":
        _no_command_fallback()
        return None

    # Unknown command
    raise DispatchError(f"Unknown command: {command!r}")


def _no_command_fallback():
    """
    Display help information when no command is provided and no "" command
    is registered.

    Per spec, this displays:
        - Application name, version, and short description
        - Long description (if available)
        - List of available commands with short descriptions
    """
    app = appmodel.application
    app_id = app["id"]

    # Application identity
    name = app_id["name"]
    version = app_id["version"]
    short_desc = app_id["short_desc"]
    long_desc = app_id["long_desc"]

    # Header
    if short_desc:
        print(f"{name} v{version} - {short_desc}")
    else:
        print(f"{name} v{version}")

    # Long description
    if long_desc:
        print()
        print(long_desc)

    # Commands
    commands = app["commands"]
    if commands:
        print()
        print("Commands:")
        for cmd_name, cmd_schema in sorted(commands.items()):
            if cmd_name == "":
                continue  # Don't list the no-command handler
            short = cmd_schema.get("short") or ""
            if short:
                print(f"  {cmd_name:20} {short}")
            else:
                print(f"  {cmd_name}")
    else:
        print()
        print("No commands available.")
