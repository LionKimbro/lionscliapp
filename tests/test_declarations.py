"""Tests for lionscliapp.declarations module."""

import pytest
import lionscliapp as app
from lionscliapp import application as appmodel
from lionscliapp import runtime_state
from lionscliapp import declarations


def setup_function():
    """Reset application and runtime state before each test."""
    app.reset()


# --- declare_app tests ---

def test_declare_app_sets_name_and_version():
    """declare_app() sets id.name and id.version."""
    declarations.declare_app("mytool", "1.0.0")

    assert appmodel.application["id"]["name"] == "mytool"
    assert appmodel.application["id"]["version"] == "1.0.0"


def test_declare_app_overwrites_previous_values():
    """declare_app() overwrites previously declared values."""
    declarations.declare_app("old", "0.1")
    declarations.declare_app("new", "2.0")

    assert appmodel.application["id"]["name"] == "new"
    assert appmodel.application["id"]["version"] == "2.0"


# --- describe_app tests ---

def test_describe_app_sets_short_desc_by_default():
    """describe_app() sets short_desc when flags is empty."""
    declarations.describe_app("A short description")

    assert appmodel.application["id"]["short_desc"] == "A short description"


def test_describe_app_sets_short_desc_with_s_flag():
    """describe_app() sets short_desc when flags contains 's'."""
    declarations.describe_app("Short one", flags="s")

    assert appmodel.application["id"]["short_desc"] == "Short one"


def test_describe_app_sets_long_desc_with_l_flag():
    """describe_app() sets long_desc when flags contains 'l'."""
    declarations.describe_app("A lengthy description", flags="l")

    assert appmodel.application["id"]["long_desc"] == "A lengthy description"


# --- declare_projectdir tests ---

def test_declare_projectdir_sets_project_dir():
    """declare_projectdir() sets names.project_dir."""
    declarations.declare_projectdir(".mytool")

    assert appmodel.application["names"]["project_dir"] == ".mytool"


# --- declare_cmd tests ---

def test_declare_cmd_creates_command_entry():
    """declare_cmd() creates a command entry with all required keys."""
    def my_fn():
        pass

    declarations.declare_cmd("run", my_fn)

    assert "run" in appmodel.application["commands"]
    assert appmodel.application["commands"]["run"]["fn"] is my_fn
    assert "short" in appmodel.application["commands"]["run"]
    assert "long" in appmodel.application["commands"]["run"]


def test_declare_cmd_binds_fn_to_existing_entry():
    """declare_cmd() binds fn to an entry created by describe_cmd."""
    def my_fn():
        pass

    declarations.describe_cmd("run", "Run the thing")
    declarations.declare_cmd("run", my_fn)

    assert appmodel.application["commands"]["run"]["fn"] is my_fn
    assert appmodel.application["commands"]["run"]["short"] == "Run the thing"


def test_declare_cmd_accepts_empty_string_for_no_command():
    """declare_cmd() accepts empty string for no-command dispatch."""
    def default_fn():
        pass

    declarations.declare_cmd("", default_fn)

    assert "" in appmodel.application["commands"]
    assert appmodel.application["commands"][""]["fn"] is default_fn


# --- describe_cmd tests ---

def test_describe_cmd_creates_entry_with_required_keys():
    """describe_cmd() creates command entry with all required keys."""
    declarations.describe_cmd("build", "Build the project")

    assert "build" in appmodel.application["commands"]
    assert appmodel.application["commands"]["build"]["short"] == "Build the project"
    assert "fn" in appmodel.application["commands"]["build"]
    assert "long" in appmodel.application["commands"]["build"]


def test_describe_cmd_sets_long_with_l_flag():
    """describe_cmd() sets long description when flags contains 'l'."""
    declarations.describe_cmd("build", "Detailed build instructions", flags="l")

    assert appmodel.application["commands"]["build"]["long"] == "Detailed build instructions"


# --- declare_key tests ---

def test_declare_key_creates_option_entry():
    """declare_key() creates an option entry with all required keys."""
    declarations.declare_key("path.output", "/tmp/out")

    assert "path.output" in appmodel.application["options"]
    assert appmodel.application["options"]["path.output"]["default"] == "/tmp/out"
    assert "short" in appmodel.application["options"]["path.output"]
    assert "long" in appmodel.application["options"]["path.output"]


def test_declare_key_overwrites_default():
    """declare_key() overwrites previously declared default."""
    declarations.declare_key("path.output", "/old")
    declarations.declare_key("path.output", "/new")

    assert appmodel.application["options"]["path.output"]["default"] == "/new"


# --- describe_key tests ---

def test_describe_key_creates_entry_with_required_keys():
    """describe_key() creates option entry with all required keys."""
    declarations.describe_key("path.output", "Output path")

    assert "path.output" in appmodel.application["options"]
    assert appmodel.application["options"]["path.output"]["short"] == "Output path"
    assert "default" in appmodel.application["options"]["path.output"]
    assert "long" in appmodel.application["options"]["path.output"]


def test_describe_key_sets_long_with_l_flag():
    """describe_key() sets long description when flags contains 'l'."""
    declarations.describe_key("path.output", "Detailed output path info", flags="l")

    assert appmodel.application["options"]["path.output"]["long"] == "Detailed output path info"


# --- declare tests (mass declaration) ---

def test_declare_merges_into_application():
    """declare() deep-merges spec into application."""
    declarations.declare({
        "id": {
            "name": "merged-app",
            "version": "3.0"
        }
    })

    assert appmodel.application["id"]["name"] == "merged-app"
    assert appmodel.application["id"]["version"] == "3.0"
    # Other id fields should remain from skeleton
    assert "short_desc" in appmodel.application["id"]


def test_declare_merges_recursively():
    """declare() merges dicts recursively, scalars last-value-wins."""
    declarations.declare({
        "flags": {
            "search_upwards_for_project_dir": True,
            "custom_flag": True
        }
    })

    assert appmodel.application["flags"]["search_upwards_for_project_dir"] is True
    assert appmodel.application["flags"]["allow_execroot_override"] is True  # unchanged
    assert appmodel.application["flags"]["custom_flag"] is True  # new


def test_declare_overwrites_scalars():
    """declare() overwrites scalar values (last value wins)."""
    declarations.declare({"id": {"name": "first"}})
    declarations.declare({"id": {"name": "second"}})

    assert appmodel.application["id"]["name"] == "second"


# --- Mutation guard tests ---

def test_declare_app_raises_when_not_declaring_phase():
    """declare_app() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare_app("test", "1.0")


def test_describe_app_raises_when_not_declaring_phase():
    """describe_app() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.describe_app("test")


def test_declare_projectdir_raises_when_not_declaring_phase():
    """declare_projectdir() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare_projectdir(".test")


def test_declare_cmd_raises_when_not_declaring_phase():
    """declare_cmd() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare_cmd("test", lambda: None)


def test_describe_cmd_raises_when_not_declaring_phase():
    """describe_cmd() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.describe_cmd("test", "desc")


def test_declare_key_raises_when_not_declaring_phase():
    """declare_key() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare_key("test.key", "value")


def test_describe_key_raises_when_not_declaring_phase():
    """describe_key() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.describe_key("test.key", "desc")


def test_declare_raises_when_not_declaring_phase():
    """declare() raises when phase is not 'declaring'."""
    runtime_state._state["phase"] = "running"

    with pytest.raises(RuntimeError, match="not permitted"):
        declarations.declare({"id": {"name": "test"}})


# --- Integration: declarations produce valid application ---

def test_declared_application_validates():
    """A fully declared application passes validation."""
    def my_cmd():
        pass

    declarations.declare_app("myapp", "1.0")
    declarations.describe_app("My application")
    declarations.declare_projectdir(".myapp")
    declarations.declare_cmd("run", my_cmd)
    declarations.describe_cmd("run", "Run the app")
    declarations.declare_key("path.output", "/tmp")
    declarations.describe_key("path.output", "Output path")

    appmodel.validate_application()  # Should not raise
