"""
json_io: JSON file reading and writing utilities for user commands.

Path resolution is controlled by mode flags:
    c - configured: Resolve via ctx['path.<id>'] (default)
    p - project: Resolve relative to project root directory
    e - execution_root: Resolve relative to execution root
    f - filesystem: Treat id as literal path (cwd-relative if not absolute)

Format flags (write_json only):
    0 - compact: No indentation
    2 - pretty: Indent with 2 spaces

For 'c' mode without format flag, json.indent.<id> from ctx is honored if
declared. indent=0 means compact (no whitespace). Other modes default to indent=2.

Usage:
    import lionscliapp as app

    # Configured path (from ctx)
    app.declare_key("path.inventory", "./inventory.json")
    data = app.read_json("inventory")        # mode='c' (default)
    app.write_json("inventory", data, "c2")  # configured path, indent=2

    # Project-relative path
    app.write_json("state.json", state, "p") # writes to <project_dir>/state.json

    # Execution-root-relative path
    app.write_json("output.json", data, "e0") # compact, in execroot

    # Literal filesystem path
    app.write_json("/tmp/debug.json", data, "f2")
"""

import json

from lionscliapp.paths import get_path, PATH_MODES
from lionscliapp.ctx import ctx


# Default indentation level for JSON output
DEFAULT_INDENT = 2

# Valid format flags for write_json
FORMAT_FLAGS = frozenset("02")


def read_json(id: str, mode: str = "c"):
    """
    Read and parse a JSON file.

    Args:
        id: Path identifier or literal path (depending on mode).
        mode: Path resolution mode (c, p, e, f). Default: 'c'.
            Format flags are not allowed for read_json.

    Returns:
        The parsed JSON data.

    Raises:
        ValueError: If mode is invalid or contains format flags.
        KeyError: If mode is 'c' and path.<id> is not declared.
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path_flag, format_flag = _parse_mode(mode)

    if format_flag is not None:
        raise ValueError(
            f"Format flags not allowed for read_json: {mode!r}"
        )

    path = get_path(id, path_flag)
    content = path.read_text(encoding="utf-8")
    return json.loads(content)


def write_json(id: str, data, mode: str = "c") -> None:
    """
    Write data to a JSON file.

    Args:
        id: Path identifier or literal path (depending on mode).
        data: JSON-serializable data to write.
        mode: Mode string with path flag and optional format flag.
            Path flags: c, p, e, f (exactly one required)
            Format flags: 0 (compact), 2 (indent=2) (optional)
            Default: 'c' (configured path, formatting from ctx or indent=2)

    Raises:
        ValueError: If mode is invalid.
        KeyError: If mode is 'c' and path.<id> is not declared.
        TypeError: If data is not JSON-serializable.
    """
    path_flag, format_flag = _parse_mode(mode)

    path = get_path(id, path_flag)
    indent, compact = _resolve_formatting(id, path_flag, format_flag)

    if compact:
        content = json.dumps(data, separators=(",", ":"))
    else:
        content = json.dumps(data, indent=indent)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content + "\n", encoding="utf-8")


def _parse_mode(mode: str) -> tuple:
    """
    Parse mode string into path_flag and format_flag.

    Returns:
        (path_flag, format_flag) where format_flag may be None.

    Raises:
        ValueError: If mode is invalid.
    """
    if not mode:
        raise ValueError("Mode string cannot be empty")

    path_flag = None
    format_flag = None

    for char in mode:
        if char in PATH_MODES:
            if path_flag is not None:
                raise ValueError(
                    f"Multiple path flags in mode: {mode!r}"
                )
            path_flag = char
        elif char in FORMAT_FLAGS:
            if format_flag is not None:
                raise ValueError(
                    f"Multiple format flags in mode: {mode!r}"
                )
            format_flag = char
        else:
            raise ValueError(
                f"Unknown flag '{char}' in mode: {mode!r}"
            )

    if path_flag is None:
        raise ValueError(
            f"Mode must contain exactly one path flag (c, p, e, f): {mode!r}"
        )

    return path_flag, format_flag


def _resolve_formatting(id: str, path_flag: str, format_flag: str | None) -> tuple:
    """
    Determine formatting parameters for write_json.

    Returns:
        (indent, compact) tuple.

    For 'c' mode without format flag, checks ctx for json.rendering.<id>
    and json.indent.<id>. Other modes default to DEFAULT_INDENT.
    """
    # Explicit format flag takes priority
    if format_flag == "0":
        return (None, True)  # compact
    elif format_flag == "2":
        return (DEFAULT_INDENT, False)

    # No format flag: check ctx for 'c' mode, else default
    if path_flag == "c":
        return _get_configured_formatting(id)
    else:
        return (DEFAULT_INDENT, False)


def _get_configured_formatting(id: str) -> tuple:
    """
    Get formatting from ctx for configured mode.

    Checks json.indent.<id>. indent=0 means compact (no whitespace).
    Defaults to DEFAULT_INDENT if not configured.

    Returns:
        (indent, compact) tuple.
    """
    indent_key = f"json.indent.{id}"
    indent = ctx.get(indent_key)

    if indent is not None:
        if indent == 0:
            return (None, True)
        return (indent, False)

    # Default
    return (DEFAULT_INDENT, False)
