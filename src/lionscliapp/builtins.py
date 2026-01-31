"""
builtins: Built-in command implementations.

Built-in commands are:
    set <key> <value>   - Persist a configuration value
    get <key>           - Display a configuration value
    help [command]      - Show help for commands and options

Built-in commands are checked before user-declared commands and cannot
be shadowed.
"""

from lionscliapp import application as appmodel
from lionscliapp import cli_state
from lionscliapp import config_io
from lionscliapp.ctx import ctx, _coerce_value


BUILTIN_COMMANDS = frozenset({"set", "get", "help"})


def is_builtin(command: str) -> bool:
    """Return True if command is a built-in command name."""
    return command in BUILTIN_COMMANDS


def run_builtin(command: str):
    """
    Dispatch to the appropriate built-in command function.

    Args:
        command: The built-in command name.

    Returns:
        Whatever the command function returns.
    """
    if command == "set":
        return cmd_set()
    elif command == "get":
        return cmd_get()
    elif command == "help":
        return cmd_help()


# =============================================================================
# set command
# =============================================================================

def cmd_set():
    """
    Persist a configuration value.

    Reads key and value from cli_state.g, validates the key exists in
    declared options, stores the value in config.json, and updates ctx.
    """
    key = cli_state.g["key"]
    value = cli_state.g["value"]

    _validate_key_exists(key)

    # Store raw value in config
    config_io.raw_config["options"][key] = value

    # Write to disk
    config_io.write_config()

    # Update ctx with coerced value
    ctx[key] = _coerce_value(key, value)

    print(f"Set {key} = {value!r}")


# =============================================================================
# get command
# =============================================================================

def cmd_get():
    """
    Display a configuration value.

    Shows the default value, config file value (if set), and current
    runtime value from ctx.
    """
    key = cli_state.g["key"]

    _validate_key_exists(key)

    options = appmodel.application["options"]
    default = options[key]["default"]
    config_value = config_io.raw_config["options"].get(key)
    current = ctx.get(key)

    print(f"{key}:")
    print(f"  default: {default!r}")
    if config_value is not None:
        print(f"  config:  {config_value!r}")
    else:
        print(f"  config:  (not set)")
    print(f"  current: {current!r}")


# =============================================================================
# help command
# =============================================================================

def cmd_help():
    """
    Show help for commands and options.

    If a specific command is requested (cli_state.g["command_help"]),
    shows detailed help for that command. Otherwise shows general help
    including all commands and declared options.
    """
    command_help = cli_state.g["command_help"]

    if command_help is not None:
        _show_command_help(command_help)
    else:
        _show_general_help()


def _show_command_help(command: str):
    """Show detailed help for a specific command."""
    # Check built-in commands first
    if command in BUILTIN_COMMANDS:
        _show_builtin_help(command)
        return

    # Check user commands
    commands = appmodel.application["commands"]
    if command in commands:
        _show_user_command_help(command, commands[command])
        return

    print(f"Unknown command: {command!r}")
    print()
    print("Use 'help' to see available commands.")


def _show_builtin_help(command: str):
    """Show help for a built-in command."""
    if command == "set":
        print("set <key> <value>")
        print()
        print("Persist a configuration value to config.json.")
        print()
        print("The key must be a declared option. The value is stored as-is")
        print("and coerced according to the key's namespace when loaded.")
        print()
        print("Example:")
        print("  set path.output /tmp/results")

    elif command == "get":
        print("get <key>")
        print()
        print("Display a configuration value.")
        print()
        print("Shows the default value, the value in config.json (if set),")
        print("and the current runtime value after coercion.")
        print()
        print("Example:")
        print("  get path.output")

    elif command == "help":
        print("help [command]")
        print()
        print("Show help for commands and options.")
        print()
        print("Without an argument, displays general help including all")
        print("available commands and declared options.")
        print()
        print("With a command name, shows detailed help for that command.")
        print()
        print("Example:")
        print("  help")
        print("  help set")


def _show_user_command_help(name: str, cmd_schema: dict):
    """Show help for a user-declared command."""
    short = cmd_schema.get("short")
    long_desc = cmd_schema.get("long")

    print(f"{name}")
    if short:
        print()
        print(short)
    if long_desc:
        print()
        print(long_desc)
    if not short and not long_desc:
        print()
        print("(No description available)")


def _show_general_help():
    """Show general help with all commands and options."""
    app = appmodel.application
    app_id = app["id"]

    # Header
    name = app_id["name"]
    version = app_id["version"]
    short_desc = app_id["short_desc"]
    long_desc = app_id["long_desc"]

    if short_desc:
        print(f"{name} v{version} - {short_desc}")
    else:
        print(f"{name} v{version}")

    if long_desc:
        print()
        print(long_desc)

    # Built-in commands
    print()
    print("Built-in commands:")
    print(f"  {'set <key> <value>':24} Persist a configuration value")
    print(f"  {'get <key>':24} Display a configuration value")
    print(f"  {'help [command]':24} Show this help")

    # User commands
    commands = app["commands"]
    user_commands = {k: v for k, v in commands.items() if k != ""}
    if user_commands:
        print()
        print("Commands:")
        for cmd_name, cmd_schema in sorted(user_commands.items()):
            short = cmd_schema.get("short") or ""
            if short:
                print(f"  {cmd_name:24} {short}")
            else:
                print(f"  {cmd_name}")

    # Options
    options = app["options"]
    if options:
        print()
        print("Options:")
        for opt_key, opt_schema in sorted(options.items()):
            default = opt_schema["default"]
            short = opt_schema.get("short") or ""
            if short:
                print(f"  {opt_key:24} {short} (default: {default!r})")
            else:
                print(f"  {opt_key:24} (default: {default!r})")


# =============================================================================
# Helpers
# =============================================================================

def _validate_key_exists(key: str):
    """
    Validate that a key exists in declared options.

    Raises:
        ValueError: If key is not declared.
    """
    options = appmodel.application["options"]
    if key not in options:
        declared = sorted(options.keys())
        if declared:
            print(f"Unknown option: {key!r}")
            print()
            print("Declared options:")
            for k in declared:
                print(f"  {k}")
        else:
            print(f"Unknown option: {key!r}")
            print()
            print("No options are declared for this application.")
        raise ValueError(f"Unknown option key: {key!r}")
