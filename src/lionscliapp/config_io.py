"""
config_io: Sole interface for reading and writing the project's raw config file.

This module handles filesystem I/O and JSON serialization only. It does NOT
perform schema validation, option coercion, ctx construction, CLI parsing,
or default merging beyond minimal structural guarantees.

The config file is always located via paths.get_config_path().
"""

import json

from lionscliapp.paths import get_config_path
from lionscliapp import file_io


raw_config = {}


def load_config():
    """
    Load config.json from disk if it exists.

    Updates raw_config to contain at least {"options": {}}.

    If the file does not exist, sets raw_config to {"options": {}} without
    writing to disk.
    If the file contains invalid JSON, raises an exception.

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON.
        RuntimeError: If the file exists but does not contain a JSON object.
    """
    config_path = get_config_path()

    if not config_path.exists():
        raw_config.clear()
        raw_config["options"] = {}
        return

    try:
        content = config_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in config file: {config_path}",
            e.doc,
            e.pos
        )

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Config file must contain a JSON object, got {type(data).__name__}: {config_path}"
        )

    if "options" not in data:
        data["options"] = {}

    raw_config.clear()
    raw_config.update(data)


def write_config():
    """
    Persist the current raw_config to disk atomically.

    Uses file_io for atomic writes. Output is UTF-8, indent=2, sort_keys=True.
    """
    config_path = get_config_path()

    content = json.dumps(raw_config, indent=2, sort_keys=True)

    f = file_io.prepare_write()
    f.write(content)
    f.write("\n")
    file_io.complete_write(config_path)


def reset_config():
    """
    Reset raw_config to an empty state (used for tests).
    """
    raw_config.clear()
