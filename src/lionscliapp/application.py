"""
application: Program-declared contract defining identity, configuration schema, and supported commands.

This module implements the data_models.application structure from the spec.
The application model is represented as a plain Python dict (no classes).

Required keys: id, names, flags, options, commands

Invariants:
    - Callable values may appear only in application["commands"][*]["fn"].
    - No other values may be callable or non-JSON-serializable.
    - JSON-serializable means: values must be composed only of dict, list, str, int, float, bool, or None.

Usage:
    from lionscliapp import application as appmodel

    appmodel.reset_application()  # Initialize to empty skeleton
    # ... make declarations ...
    appmodel.validate_application()  # Validate before main()

    # Read the global:
    print(appmodel.application["id"]["name"])
"""

# The global application dictionary.
# Always the same dict object; use reset_application() to clear and reinitialize.
application = {}

# Validation errors accumulator. Cleared in place at start of validate_application().
_errors = []


def reset_application():
    """
    Reinitialize the global application dictionary to a valid empty skeleton.

    The skeleton contains all required keys with default values:
    - id: empty name/version strings, null descriptions
    - names: empty project_dir string
    - flags: default flag values from spec
    - options: empty dict
    - commands: empty dict

    Also clears any residual validation state.

    Note: Mutates in place; does not reassign the global.
    """
    del _errors[:]
    application.clear()
    application.update({
        "id": {
            "name": "",
            "version": "",
            "short_desc": None,
            "long_desc": None
        },
        "names": {
            "project_dir": ""
        },
        "flags": {
            "search_upwards_for_project_dir": False,
            "allow_execroot_override": True
        },
        "options": {},
        "commands": {}
    })


def validate_application():
    """
    Validate the global application dictionary against the spec schema.

    Checks:
    - All required keys are present
    - All values have correct types
    - Only application["commands"][*]["fn"] may contain callables
    - All other values must be JSON-serializable

    Raises:
        ValueError: If validation fails, with a message describing all errors.
        RuntimeError: If application has not been initialized.
    """
    del _errors[:]

    if not application:
        raise RuntimeError(
            "Application not initialized. Call reset_application() first."
        )

    # Check top-level required keys
    required_top_keys = ["id", "names", "flags", "options", "commands"]
    for key in required_top_keys:
        if key not in application:
            _errors.append(f"Missing required key: {key}")

    # If missing required keys, can't continue validation
    if _errors:
        raise ValueError(
            "Application validation failed:\n" +
            "\n".join(f"  - {e}" for e in _errors)
        )

    _validate_id()
    _validate_names()
    _validate_flags()
    _validate_options()
    _validate_commands()
    _check_no_callables_outside_commands()

    if _errors:
        raise ValueError(
            "Application validation failed:\n" +
            "\n".join(f"  - {e}" for e in _errors)
        )


def _validate_id():
    """Validate the id section."""
    id_obj = application["id"]

    if not isinstance(id_obj, dict):
        _errors.append("id: must be a dict")
        return

    # Required string fields
    for field in ["name", "version"]:
        if field not in id_obj:
            _errors.append(f"id.{field}: missing required field")
        elif not isinstance(id_obj[field], str):
            _errors.append(f"id.{field}: must be a string")

    # Required string-or-null fields
    for field in ["short_desc", "long_desc"]:
        if field not in id_obj:
            _errors.append(f"id.{field}: missing required field")
        else:
            val = id_obj[field]
            if val is not None and not isinstance(val, str):
                _errors.append(f"id.{field}: must be a string or null")


def _validate_names():
    """Validate the names section."""
    names_obj = application["names"]

    if not isinstance(names_obj, dict):
        _errors.append("names: must be a dict")
        return

    if "project_dir" not in names_obj:
        _errors.append("names.project_dir: missing required field")
    elif not isinstance(names_obj["project_dir"], str):
        _errors.append("names.project_dir: must be a string")
    elif names_obj["project_dir"] == "":
        _errors.append("names.project_dir: must not be empty")


def _validate_flags():
    """Validate the flags section."""
    flags_obj = application["flags"]

    if not isinstance(flags_obj, dict):
        _errors.append("flags: must be a dict")
        return

    for key, val in flags_obj.items():
        if not isinstance(key, str):
            _errors.append(f"flags: key {key!r} must be a string")
        if not isinstance(val, bool):
            _errors.append(f"flags.{key}: must be a boolean")


def _validate_options():
    """Validate the options section."""
    options_obj = application["options"]

    if not isinstance(options_obj, dict):
        _errors.append("options: must be a dict")
        return

    for opt_key, opt_schema in options_obj.items():
        if not isinstance(opt_key, str):
            _errors.append(f"options: key {opt_key!r} must be a string")
            continue
        if not isinstance(opt_schema, dict):
            _errors.append(f"options.{opt_key}: must be a dict")
            continue

        # Required: default (JSON-serializable value)
        if "default" not in opt_schema:
            _errors.append(f"options.{opt_key}.default: missing required field")
        else:
            _check_json_serializable(
                opt_schema["default"],
                f"options.{opt_key}.default"
            )

        # Required: short, long (must be string or null)
        for field in ["short", "long"]:
            if field not in opt_schema:
                _errors.append(f"options.{opt_key}.{field}: missing required field")
            else:
                val = opt_schema[field]
                if val is not None and not isinstance(val, str):
                    _errors.append(f"options.{opt_key}.{field}: must be a string or null")


def _validate_commands():
    """Validate the commands section."""
    commands_obj = application["commands"]

    if not isinstance(commands_obj, dict):
        _errors.append("commands: must be a dict")
        return

    for cmd_name, cmd_schema in commands_obj.items():
        if not isinstance(cmd_name, str):
            _errors.append(f"commands: key {cmd_name!r} must be a string")
            continue
        if not isinstance(cmd_schema, dict):
            _errors.append(f"commands.{cmd_name}: must be a dict")
            continue

        # Required: fn (may be null or callable)
        if "fn" not in cmd_schema:
            _errors.append(f"commands.{cmd_name}.fn: missing required field")
        else:
            fn_val = cmd_schema["fn"]
            if fn_val is not None and not callable(fn_val):
                _errors.append(f"commands.{cmd_name}.fn: must be null or callable")

        # Required: short, long (must be string or null)
        for field in ["short", "long"]:
            if field not in cmd_schema:
                _errors.append(f"commands.{cmd_name}.{field}: missing required field")
            else:
                val = cmd_schema[field]
                if val is not None and not isinstance(val, str):
                    _errors.append(f"commands.{cmd_name}.{field}: must be a string or null")


def _check_json_serializable(value, path):
    """
    Recursively check that a value is JSON-serializable.

    JSON-serializable means: dict, list, str, int, float, bool, or None.

    Appends to _errors for any non-serializable values found.
    """
    if value is None:
        return

    if isinstance(value, bool):
        # Must check bool before int because bool is a subclass of int
        return

    if isinstance(value, (str, int, float)):
        return

    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                _errors.append(f"{path}: dict key {k!r} is not a string")
            _check_json_serializable(v, f"{path}.{k}")
        return

    if isinstance(value, list):
        for i, item in enumerate(value):
            _check_json_serializable(item, f"{path}[{i}]")
        return

    # Not a JSON-serializable type
    _errors.append(
        f"{path}: value {value!r} is not JSON-serializable "
        f"(type: {type(value).__name__})"
    )


def _check_no_callables_outside_commands():
    """
    Check invariant: no callables except in commands[*].fn.

    Appends to _errors for any callables found in wrong locations.
    """
    # Check id, names, flags
    for section in ["id", "names", "flags"]:
        _check_no_callables(application[section], section)

    # Check options (entire option schemas must be JSON-serializable)
    for opt_key, opt_schema in application["options"].items():
        _check_no_callables(opt_schema, f"options.{opt_key}")

    # Check commands - but skip fn field
    for cmd_name, cmd_schema in application["commands"].items():
        for field, val in cmd_schema.items():
            if field == "fn":
                continue  # fn is allowed to be callable
            _check_no_callables(val, f"commands.{cmd_name}.{field}")


def _check_no_callables(value, path):
    """
    Recursively check that a value contains no callables.

    Appends to _errors for any callables found.
    """
    if callable(value):
        _errors.append(
            f"{path}: contains callable (not allowed outside commands[*].fn)"
        )
        return

    if isinstance(value, dict):
        for k, v in value.items():
            _check_no_callables(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _check_no_callables(item, f"{path}[{i}]")


def ensure_commands_bound():
    """
    Verify all declared commands have their fn field bound to a callable.

    Called by main() before transitioning to running phase.

    Raises:
        RuntimeError: If any command has fn=None.
    """
    unbound = []
    for cmd_name, cmd_schema in application["commands"].items():
        if cmd_schema.get("fn") is None:
            unbound.append(cmd_name)

    if unbound:
        cmd_list = ", ".join(repr(name) for name in sorted(unbound))
        raise RuntimeError(
            f"Commands with unbound fn: {cmd_list}. "
            f"All commands must have fn bound before calling main()."
        )


reset_application()

