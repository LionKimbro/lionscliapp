"""Tests for lionscliapp.application module."""

import pytest
from lionscliapp import application as appmodel


def setup_function():
    """Reset application state before each test."""
    appmodel.application.clear()
    del appmodel._errors[:]


def test_reset_application_creates_valid_skeleton():
    """reset_application() creates a structurally valid skeleton."""
    appmodel.reset_application()

    assert appmodel.application is not None
    assert "id" in appmodel.application
    assert "names" in appmodel.application
    assert "flags" in appmodel.application
    assert "options" in appmodel.application
    assert "commands" in appmodel.application


def test_reset_application_sets_default_flags():
    """reset_application() sets spec-defined default flag values."""
    appmodel.reset_application()

    flags = appmodel.application["flags"]
    assert flags["search_upwards_for_project_dir"] is False
    assert flags["allow_execroot_override"] is True


def test_reset_application_skeleton_requires_project_dir():
    """The empty skeleton from reset_application() requires project_dir to be set."""
    appmodel.reset_application()

    with pytest.raises(ValueError, match="names.project_dir: must not be empty"):
        appmodel.validate_application()


def test_validate_application_raises_if_not_initialized():
    """validate_application() raises RuntimeError if application is empty."""
    appmodel.application.clear()

    with pytest.raises(RuntimeError, match="not initialized"):
        appmodel.validate_application()


def test_validate_application_catches_missing_top_level_keys():
    """validate_application() catches missing required top-level keys."""
    appmodel.application.clear()
    appmodel.application.update({"id": {}})  # Missing names, flags, options, commands

    with pytest.raises(ValueError, match="Missing required key"):
        appmodel.validate_application()


def test_validate_application_catches_invalid_id_type():
    """validate_application() catches when id is not a dict."""
    appmodel.reset_application()
    appmodel.application["id"] = "not a dict"

    with pytest.raises(ValueError, match="id: must be a dict"):
        appmodel.validate_application()


def test_validate_application_catches_missing_id_fields():
    """validate_application() catches missing required id fields."""
    appmodel.reset_application()
    del appmodel.application["id"]["name"]

    with pytest.raises(ValueError, match="id.name: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_invalid_id_field_types():
    """validate_application() catches wrong types in id fields."""
    appmodel.reset_application()
    appmodel.application["id"]["name"] = 123  # Should be string

    with pytest.raises(ValueError, match="id.name: must be a string"):
        appmodel.validate_application()


def test_validate_application_catches_invalid_flag_type():
    """validate_application() catches non-boolean flag values."""
    appmodel.reset_application()
    appmodel.application["flags"]["allow_execroot_override"] = "yes"

    with pytest.raises(ValueError, match="must be a boolean"):
        appmodel.validate_application()


def test_validate_application_accepts_valid_options():
    """validate_application() accepts properly structured options."""
    appmodel.reset_application()
    appmodel.application["names"]["project_dir"] = ".myapp"
    appmodel.application["options"]["path.scan"] = {
        "default": "/tmp",
        "short": "Scan path",
        "long": None
    }

    appmodel.validate_application()  # Should not raise


def test_validate_application_catches_missing_option_default():
    """validate_application() catches options missing required default field."""
    appmodel.reset_application()
    appmodel.application["options"]["path.scan"] = {
        "short": "Scan path",
        "long": None
        # Missing "default"
    }

    with pytest.raises(ValueError, match="options.path.scan.default: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_non_json_serializable_default():
    """validate_application() catches non-JSON-serializable option defaults."""
    appmodel.reset_application()
    appmodel.application["options"]["bad.option"] = {
        "default": lambda: None,  # Callable is not JSON-serializable
        "short": None,
        "long": None
    }

    with pytest.raises(ValueError, match="not JSON-serializable"):
        appmodel.validate_application()


def test_validate_application_accepts_valid_commands():
    """validate_application() accepts properly structured commands."""
    def my_cmd():
        pass

    appmodel.reset_application()
    appmodel.application["names"]["project_dir"] = ".myapp"
    appmodel.application["commands"]["run"] = {
        "fn": my_cmd,
        "short": "Run the thing",
        "long": None
    }

    appmodel.validate_application()  # Should not raise


def test_validate_application_accepts_null_command_fn():
    """validate_application() accepts null fn (placeholder) in commands."""
    appmodel.reset_application()
    appmodel.application["names"]["project_dir"] = ".myapp"
    appmodel.application["commands"]["run"] = {
        "fn": None,
        "short": "Run the thing",
        "long": None
    }

    appmodel.validate_application()  # Should not raise


def test_validate_application_catches_missing_command_fn():
    """validate_application() catches commands missing required fn field."""
    appmodel.reset_application()
    appmodel.application["commands"]["run"] = {
        "short": "Run the thing",
        "long": None
        # Missing "fn"
    }

    with pytest.raises(ValueError, match="commands.run.fn: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_invalid_command_fn():
    """validate_application() catches fn that is neither null nor callable."""
    appmodel.reset_application()
    appmodel.application["commands"]["run"] = {
        "fn": "not callable",
        "short": None,
        "long": None
    }

    with pytest.raises(ValueError, match="commands.run.fn: must be null or callable"):
        appmodel.validate_application()


def test_validate_application_catches_callable_outside_commands_fn():
    """validate_application() catches callables outside commands[*].fn."""
    appmodel.reset_application()
    appmodel.application["id"]["name"] = lambda: "bad"

    with pytest.raises(ValueError, match="contains callable"):
        appmodel.validate_application()


def test_validate_application_catches_callable_in_option_default():
    """validate_application() catches callable in option default."""
    appmodel.reset_application()
    appmodel.application["options"]["bad"] = {
        "default": print,  # Callable
        "short": None,
        "long": None
    }

    with pytest.raises(ValueError, match="not JSON-serializable"):
        appmodel.validate_application()


def test_validate_application_catches_callable_in_command_short():
    """validate_application() catches callable in command description field."""
    def my_cmd():
        pass

    appmodel.reset_application()
    appmodel.application["commands"]["run"] = {
        "fn": my_cmd,
        "short": lambda: "bad",  # Callable not allowed here
        "long": None
    }

    with pytest.raises(ValueError, match="contains callable"):
        appmodel.validate_application()


def test_validate_application_accepts_nested_json_in_option_default():
    """validate_application() accepts nested JSON structures in defaults."""
    appmodel.reset_application()
    appmodel.application["names"]["project_dir"] = ".myapp"
    appmodel.application["options"]["complex.option"] = {
        "default": {
            "nested": {
                "list": [1, 2, {"deep": True}],
                "value": None
            }
        },
        "short": None,
        "long": None
    }

    appmodel.validate_application()  # Should not raise


def test_reset_application_clears_previous_state():
    """reset_application() clears any previous application state completely."""
    appmodel.reset_application()
    appmodel.application["id"]["name"] = "MyApp"
    appmodel.application["id"]["version"] = "1.0"
    appmodel.application["id"]["short_desc"] = "My application"
    appmodel.application["names"]["project_dir"] = ".myapp"
    appmodel.application["flags"]["custom_flag"] = True
    appmodel.application["options"]["path.scan"] = {"default": "/tmp"}
    appmodel.application["commands"]["foo"] = {"fn": lambda: None}

    appmodel.reset_application()

    expected_skeleton = {
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
    }
    assert appmodel.application == expected_skeleton


def test_reset_application_clears_errors():
    """reset_application() clears residual validation errors."""
    # Force some errors into _errors (in place)
    appmodel._errors.extend(["some old error", "another old error"])

    appmodel.reset_application()

    assert appmodel._errors == []


def test_validate_application_catches_missing_id_short_desc():
    """validate_application() catches missing short_desc in id."""
    appmodel.reset_application()
    del appmodel.application["id"]["short_desc"]

    with pytest.raises(ValueError, match="id.short_desc: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_missing_id_long_desc():
    """validate_application() catches missing long_desc in id."""
    appmodel.reset_application()
    del appmodel.application["id"]["long_desc"]

    with pytest.raises(ValueError, match="id.long_desc: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_missing_option_short():
    """validate_application() catches missing short in option schema."""
    appmodel.reset_application()
    appmodel.application["options"]["path.scan"] = {
        "default": "/tmp",
        "long": None
        # Missing "short"
    }

    with pytest.raises(ValueError, match="options.path.scan.short: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_missing_option_long():
    """validate_application() catches missing long in option schema."""
    appmodel.reset_application()
    appmodel.application["options"]["path.scan"] = {
        "default": "/tmp",
        "short": "Scan path"
        # Missing "long"
    }

    with pytest.raises(ValueError, match="options.path.scan.long: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_missing_command_short():
    """validate_application() catches missing short in command schema."""
    appmodel.reset_application()
    appmodel.application["commands"]["run"] = {
        "fn": None,
        "long": None
        # Missing "short"
    }

    with pytest.raises(ValueError, match="commands.run.short: missing required field"):
        appmodel.validate_application()


def test_validate_application_catches_missing_command_long():
    """validate_application() catches missing long in command schema."""
    appmodel.reset_application()
    appmodel.application["commands"]["run"] = {
        "fn": None,
        "short": "Run the thing"
        # Missing "long"
    }

    with pytest.raises(ValueError, match="commands.run.long: missing required field"):
        appmodel.validate_application()
