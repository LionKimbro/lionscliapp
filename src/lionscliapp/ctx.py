"""
ctx: Merged and coerced runtime execution context.

This module constructs the ctx dictionary that commands use to access
configuration at runtime. The ctx is built by:

1. Starting with declared defaults from application["options"]
2. Overlaying raw_config["options"]
3. Overlaying override_inputs.options_file_overrides
4. Overlaying override_inputs.cli_overrides
5. Coercing values by namespace policies

Namespace coercion rules (from spec):
    path.*           -> pathlib.Path (expanduser, relative resolved against execroot)
    json.rendering.* -> validated enum ("pretty", "compact")
    json.indent.*    -> int >= 0
    (unknown)        -> identity (no coercion)

The ctx is constructed during main() after config loading, before command
dispatch. Commands access it via app.ctx.
"""

from pathlib import Path

from lionscliapp.application import application
from lionscliapp import config_io
from lionscliapp import override_inputs
from lionscliapp import execroot


ctx = {}


def build_ctx():
    """
    Construct ctx by merging layers and applying namespace coercion.

    Merge order (later wins):
        1. Declared defaults (application["options"][key]["default"])
        2. Config file values (raw_config["options"])
        3. Options file overrides (override_inputs.options_file_overrides)
        4. CLI overrides (override_inputs.cli_overrides)

    After merging, values are coerced by namespace prefix.

    Modifies the global ctx dict in place.
    """
    ctx.clear()

    # Layer 1: Defaults
    for key, opt_schema in application["options"].items():
        ctx[key] = opt_schema["default"]

    # Layer 2: Config file
    for key, value in config_io.raw_config.get("options", {}).items():
        if key in ctx:
            ctx[key] = value

    # Layer 3: Options file overrides
    for key, value in override_inputs.options_file_overrides.items():
        if key in ctx:
            ctx[key] = value

    # Layer 4: CLI overrides
    for key, value in override_inputs.cli_overrides.items():
        if key in ctx:
            ctx[key] = value

    # Coerce all values by namespace
    for key in ctx:
        ctx[key] = _coerce_value(key, ctx[key])


def _coerce_value(key, value):
    """
    Coerce a value according to its namespace prefix.

    Args:
        key: The dot-namespaced option key (e.g., "path.output")
        value: The raw value to coerce

    Returns:
        The coerced value.

    Raises:
        ValueError: If the value cannot be coerced to the expected type.
    """
    namespace = _get_namespace(key)

    if namespace == "path":
        return _coerce_path(key, value)
    elif namespace == "json.rendering":
        return _coerce_json_rendering(key, value)
    elif namespace == "json.indent":
        return _coerce_json_indent(key, value)
    else:
        # Unknown namespace: identity (no coercion)
        return value


def _get_namespace(key):
    """
    Extract the namespace prefix from a dot-namespaced key.

    Special handling for multi-level namespaces like "json.rendering".

    Args:
        key: The dot-namespaced option key

    Returns:
        The namespace prefix string.
    """
    # Check multi-level namespaces first
    if key.startswith("json.rendering."):
        return "json.rendering"
    if key.startswith("json.indent."):
        return "json.indent"

    # Single-level namespace: prefix before first dot
    if "." in key:
        return key.split(".", 1)[0]
    return key


def _coerce_path(key, value):
    """
    Coerce a value to pathlib.Path.

    Processing:
        1. expanduser() to handle ~ paths
        2. If relative, resolve against execroot (not CWD)

    Args:
        key: The option key (for error messages)
        value: The value to coerce (must be a string)

    Returns:
        A pathlib.Path instance (absolute).

    Raises:
        ValueError: If value is not a valid path string.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"Option {key!r}: path value must be a string, got {type(value).__name__}"
        )

    p = Path(value).expanduser()

    if not p.is_absolute():
        p = execroot.get_execroot() / p

    return p


def _coerce_json_rendering(key, value):
    """
    Coerce and validate a json.rendering.* value.

    Args:
        key: The option key (for error messages)
        value: The value to validate

    Returns:
        The validated string ("pretty" or "compact").

    Raises:
        ValueError: If value is not a valid rendering mode.
    """
    allowed = ("pretty", "compact")
    if value not in allowed:
        raise ValueError(
            f"Option {key!r}: must be one of {allowed}, got {value!r}"
        )
    return value


def _coerce_json_indent(key, value):
    """
    Coerce a json.indent.* value to int.

    Args:
        key: The option key (for error messages)
        value: The value to coerce (string or number)

    Returns:
        An int >= 0.

    Raises:
        ValueError: If value cannot be converted to a non-negative int.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Option {key!r}: must be an integer, got {value!r}"
        )

    if int_value < 0:
        raise ValueError(
            f"Option {key!r}: must be >= 0, got {int_value}"
        )

    return int_value


def reset_ctx():
    """
    Reset ctx to an empty state.

    Called by app.reset() for tests.
    """
    ctx.clear()
