"""
declarations: Declaration APIs for building the application model.

All declaration functions:
- Mutate the global application dict only
- Enforce runtime_state.phase == 'declaring'
- Follow merge semantics: objects merged recursively, scalars last-value-wins

Usage:
    import lionscliapp as app

    app.declare_app("mytool", "1.0")
    app.declare_projectdir(".mytool")
    app.declare_cmd("run", my_run_function)
    app.declare_key("execpath.output", "/tmp/out")
"""

import warnings

from lionscliapp.runtime_state import require_declaring_phase
from lionscliapp.application import application


def declare_app(name, version):
    """
    Declare the name and version of the application.

    Args:
        name: Application name (string)
        version: Application version (string)
    """
    require_declaring_phase()
    application["id"]["name"] = name
    application["id"]["version"] = version


def describe_app(description, flags=""):
    """
    Declare a short or long description for the application.

    Args:
        description: Description text
        flags: "" or "s" for short_desc (default), "l" for long_desc
    """
    require_declaring_phase()
    if "l" in flags:
        application["id"]["long_desc"] = description
    else:
        application["id"]["short_desc"] = description


def declare_projectdir(name):
    """
    Declare the project directory name.

    Args:
        name: Directory name (e.g., ".mytool")
    """
    require_declaring_phase()
    application["names"]["project_dir"] = name


def declare_cmd(name, fn):
    """
    Bind a command to a callable function.

    The command entry is created if it doesn't exist (with all required keys).
    If the entry exists (e.g., from describe_cmd), the fn is bound to it.

    Args:
        name: Command name (string, or "" for no-command dispatch)
        fn: Callable to execute when command is invoked
    """
    require_declaring_phase()
    if name not in application["commands"]:
        application["commands"][name] = {
            "fn": None,
            "short": None,
            "long": None,
            "flags": {
                "locking": False
            }
        }
    application["commands"][name]["fn"] = fn


def describe_cmd(name, description, flags=""):
    """
    Declare a short or long description for a command.

    The command entry is created if it doesn't exist (with all required keys).

    Args:
        name: Command name
        description: Description text
        flags: "" or "s" for short (default), "l" for long
    """
    require_declaring_phase()
    if name not in application["commands"]:
        application["commands"][name] = {
            "fn": None,
            "short": None,
            "long": None,
            "flags": {
                "locking": False
            }
        }
    if "l" in flags:
        application["commands"][name]["long"] = description
    else:
        application["commands"][name]["short"] = description


def set_cmd_flag(name, flag_name, value):
    """
    Set a boolean flag on a specific command.

    The command entry is created if it does not yet exist, with default
    command fields and default command flags.

    Args:
        name: Command name
        flag_name: Command flag name (e.g. "locking")
        value: Boolean value to assign
    """
    require_declaring_phase()
    if not isinstance(value, bool):
        raise ValueError(
            f"set_cmd_flag: value for '{flag_name}' on command {name!r} "
            f"must be a bool, got {type(value).__name__!r}"
        )

    if name not in application["commands"]:
        application["commands"][name] = {
            "fn": None,
            "short": None,
            "long": None,
            "flags": {
                "locking": False
            }
        }

    if "flags" not in application["commands"][name]:
        application["commands"][name]["flags"] = {"locking": False}

    application["commands"][name]["flags"][flag_name] = value


def declare_key(key, default):
    """
    Declare a configuration key with its default value.

    The default value must be JSON-serializable.
    The option entry is created if it doesn't exist (with all required keys).

    Args:
        key: Option key (dot-namespaced string, e.g., "execpath.output")
        default: Default value (JSON-serializable)
    """
    require_declaring_phase()
    if key.startswith("path."):
        unprefixed = key[5:]
        warnings.warn(
            f"declare_key({key!r}, ...): the 'path.*' namespace is deprecated. "
            f"Use 'execpath.{unprefixed}' (same behavior, execroot-relative) "
            f"or 'projpath.{unprefixed}' (project-dir-relative).",
            DeprecationWarning,
            stacklevel=2,
        )
    if key not in application["options"]:
        application["options"][key] = {
            "default": None,
            "short": None,
            "long": None
        }
    application["options"][key]["default"] = default


def describe_key(key, description, flags=""):
    """
    Declare a short or long description for a configuration key.

    The option entry is created if it doesn't exist (with all required keys).

    Args:
        key: Option key
        description: Description text
        flags: "" or "s" for short (default), "l" for long
    """
    require_declaring_phase()
    if key not in application["options"]:
        application["options"][key] = {
            "default": None,
            "short": None,
            "long": None
        }
    if "l" in flags:
        application["options"][key]["long"] = description
    else:
        application["options"][key]["short"] = description


def set_flag(flag_name, value):
    """
    Set a flag in the application flags dict.

    Flags control framework behaviour (e.g. allow_projectdir_override).
    All flag values must be booleans.

    Args:
        flag_name: Flag name string (e.g. "allow_projectdir_override")
        value: Boolean value to assign
    """
    require_declaring_phase()
    if not isinstance(value, bool):
        raise ValueError(
            f"set_flag: value for '{flag_name}' must be a bool, "
            f"got {type(value).__name__!r}"
        )
    application["flags"][flag_name] = value


def declare(spec):
    """
    Perform a mass declaration by deep-merging spec into the application.

    Merge semantics:
    - Objects (dicts): merged recursively by key
    - Scalars: last value wins
    - Commands/options: entries merged, later values override

    Args:
        spec: Dictionary to merge into application
    """
    require_declaring_phase()
    _deep_merge(application, spec)


def _deep_merge(target, source):
    """
    Recursively merge source into target.

    - Dicts are merged recursively
    - All other values: source overwrites target (last value wins)
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
