"""Tests for lionscliapp.cli_parsing module."""

import pytest

import lionscliapp as app
from lionscliapp import cli_state
from lionscliapp.cli_parsing import ingest_argv


def setup_function():
    """Reset all state before each test."""
    app.reset()


# --- Empty and command-only cases ---

def test_ingest_argv_empty_leaves_defaults():
    """Empty argv leaves all state as None/empty."""
    ingest_argv([])

    assert cli_state.g["command"] is None
    assert cli_state.g["options_file"] is None
    assert cli_state.g["execroot_override"] is None
    assert cli_state.option_overrides == {}


def test_ingest_argv_command_only():
    """Single non-option token becomes command."""
    ingest_argv(["run"])

    assert cli_state.g["command"] == "run"


def test_ingest_argv_resets_state_before_parsing():
    """ingest_argv resets state at start."""
    cli_state.g["command"] = "old"
    cli_state.option_overrides["key"] = "value"

    ingest_argv(["new"])

    assert cli_state.g["command"] == "new"
    assert cli_state.option_overrides == {}


# --- Recognized options ---

def test_ingest_argv_execroot_option():
    """--execroot sets execroot_override."""
    ingest_argv(["--execroot", "/some/path"])

    assert cli_state.g["execroot_override"] == "/some/path"


def test_ingest_argv_options_file_option():
    """--options-file sets options_file."""
    ingest_argv(["--options-file", "/path/to/options.json"])

    assert cli_state.g["options_file"] == "/path/to/options.json"


def test_ingest_argv_generic_option_override():
    """--something stores in option_overrides."""
    ingest_argv(["--db.host", "localhost"])

    assert cli_state.option_overrides == {"db.host": "localhost"}


def test_ingest_argv_multiple_option_overrides():
    """Multiple generic options all stored."""
    ingest_argv(["--db.host", "localhost", "--db.port", "5432"])

    assert cli_state.option_overrides == {"db.host": "localhost", "db.port": "5432"}


# --- Combined cases ---

def test_ingest_argv_command_with_options():
    """Command can appear with options."""
    ingest_argv(["run", "--execroot", "/path"])

    assert cli_state.g["command"] == "run"
    assert cli_state.g["execroot_override"] == "/path"


def test_ingest_argv_options_before_command():
    """Options can appear before command."""
    ingest_argv(["--execroot", "/path", "run"])

    assert cli_state.g["command"] == "run"
    assert cli_state.g["execroot_override"] == "/path"


# --- Error cases ---

def test_ingest_argv_option_missing_value():
    """Option at end without value raises."""
    with pytest.raises(ValueError, match="requires a value"):
        ingest_argv(["--execroot"])


def test_ingest_argv_short_option_rejected():
    """Short options (single dash) rejected."""
    with pytest.raises(ValueError, match="Short options not supported"):
        ingest_argv(["-v"])


def test_ingest_argv_multiple_positional_rejected():
    """Second positional token raises."""
    with pytest.raises(ValueError, match="Multiple positional"):
        ingest_argv(["run", "extra"])


def test_ingest_argv_bare_double_dash_rejected():
    """Bare '--' is invalid."""
    with pytest.raises(ValueError, match="Empty option name"):
        ingest_argv(["--"])


# --- Values are raw strings ---

def test_ingest_argv_values_are_strings():
    """All values stored as raw strings, no coercion."""
    ingest_argv(["--port", "8080", "--enabled", "true"])

    assert cli_state.option_overrides["port"] == "8080"
    assert isinstance(cli_state.option_overrides["port"], str)


def test_ingest_argv_execroot_is_string():
    """execroot_override stored as string, not Path."""
    ingest_argv(["--execroot", "/some/path"])

    assert isinstance(cli_state.g["execroot_override"], str)
