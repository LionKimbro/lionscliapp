"""
json_io: JSON file reading and writing utilities for user commands.

These functions use declared options to determine file paths and formatting:
    path.<fileid>           - File location (required)
    json.rendering.<fileid> - "pretty" or "compact" (default: "pretty")
    json.indent.<fileid>    - Indentation level (default: 2)

Usage:
    import lionscliapp as app

    app.declare_key("path.inventory", "./inventory.json")
    app.declare_key("json.rendering.inventory", "pretty")
    app.declare_key("json.indent.inventory", 2)

    # In a command:
    data = app.read_json("inventory")
    data["count"] += 1
    app.write_json("inventory", data)
"""

import json

from lionscliapp.ctx import ctx


def read_json(fileid: str):
    """
    Read and parse a JSON file at the configured path.

    Args:
        fileid: Logical file identifier. Path is read from ctx["path.<fileid>"].

    Returns:
        The parsed JSON data.

    Raises:
        KeyError: If path.<fileid> is not declared.
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = _get_path(fileid)
    content = path.read_text(encoding="utf-8")
    return json.loads(content)


def write_json(fileid: str, data) -> None:
    """
    Write data to a JSON file at the configured path.

    Uses formatting options from ctx:
        json.rendering.<fileid> - "pretty" or "compact" (default: "pretty")
        json.indent.<fileid>    - Indentation level (default: 2)

    Args:
        fileid: Logical file identifier. Path is read from ctx["path.<fileid>"].
        data: JSON-serializable data to write.

    Raises:
        KeyError: If path.<fileid> is not declared.
        TypeError: If data is not JSON-serializable.
    """
    path = _get_path(fileid)
    rendering = _get_rendering(fileid)
    indent = _get_indent(fileid)

    if rendering == "compact":
        content = json.dumps(data, separators=(",", ":"))
    else:
        content = json.dumps(data, indent=indent)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content + "\n", encoding="utf-8")


def _get_path(fileid: str):
    """Get the path for a fileid from ctx."""
    key = f"path.{fileid}"
    if key not in ctx:
        raise KeyError(f"No path configured for '{fileid}': declare 'path.{fileid}'")
    return ctx[key]


def _get_rendering(fileid: str) -> str:
    """Get the rendering mode for a fileid, defaulting to 'pretty'."""
    key = f"json.rendering.{fileid}"
    return ctx.get(key, "pretty")


def _get_indent(fileid: str) -> int:
    """Get the indent level for a fileid, defaulting to 2."""
    key = f"json.indent.{fileid}"
    return ctx.get(key, 2)
