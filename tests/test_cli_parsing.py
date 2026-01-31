"""Tests for lionscliapp.cli_parsing module."""

import pytest

import lionscliapp as app
from lionscliapp import cli_state
from lionscliapp import override_inputs
from lionscliapp.cli_parsing import ingest_argv, interpret_arguments


def setup_function():
    """Reset all state before each test."""
    app.reset()


# =============================================================================
# ingest_argv tests - raw token parsing
# =============================================================================

# --- Empty and basic cases ---

def test_ingest_argv_empty():
    """Empty argv leaves positional_args empty and options as None."""
    ingest_argv([])

    assert cli_state.positional_args == []
    assert cli_state.g["options_file"] is None
    assert cli_state.g["execroot_override"] is None
    assert override_inputs.cli_overrides == {}


def test_ingest_argv_collects_positional():
    """Non-option tokens collect into positional_args."""
    ingest_argv(["run"])

    assert cli_state.positional_args == ["run"]


def test_ingest_argv_collects_multiple_positionals():
    """Multiple positional tokens all collected (interpretation happens later)."""
    ingest_argv(["set", "path.foo", "/some/path"])

    assert cli_state.positional_args == ["set", "path.foo", "/some/path"]


def test_ingest_argv_resets_state():
    """ingest_argv resets all state at start."""
    cli_state.positional_args.append("old")
    cli_state.g["options_file"] = "old.json"
    override_inputs.cli_overrides["key"] = "value"

    ingest_argv(["new"])

    assert cli_state.positional_args == ["new"]
    assert cli_state.g["options_file"] is None
    assert override_inputs.cli_overrides == {}


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
    """--something stores in cli_overrides."""
    ingest_argv(["--db.host", "localhost"])

    assert override_inputs.cli_overrides == {"db.host": "localhost"}


def test_ingest_argv_multiple_option_overrides():
    """Multiple generic options all stored."""
    ingest_argv(["--db.host", "localhost", "--db.port", "5432"])

    assert override_inputs.cli_overrides == {"db.host": "localhost", "db.port": "5432"}


# --- Mixed positionals and options ---

def test_ingest_argv_positional_with_options():
    """Positional and options can be mixed."""
    ingest_argv(["run", "--execroot", "/path"])

    assert cli_state.positional_args == ["run"]
    assert cli_state.g["execroot_override"] == "/path"


def test_ingest_argv_options_before_positional():
    """Options can appear before positional tokens."""
    ingest_argv(["--execroot", "/path", "run"])

    assert cli_state.positional_args == ["run"]
    assert cli_state.g["execroot_override"] == "/path"


def test_ingest_argv_options_between_positionals():
    """Options can appear between positional tokens."""
    ingest_argv(["set", "--execroot", "/path", "key", "value"])

    assert cli_state.positional_args == ["set", "key", "value"]
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


def test_ingest_argv_bare_double_dash_rejected():
    """Bare '--' is invalid."""
    with pytest.raises(ValueError, match="Empty option name"):
        ingest_argv(["--"])


# --- Values are raw strings ---

def test_ingest_argv_values_are_strings():
    """All values stored as raw strings, no coercion."""
    ingest_argv(["--port", "8080", "--enabled", "true"])

    assert override_inputs.cli_overrides["port"] == "8080"
    assert isinstance(override_inputs.cli_overrides["port"], str)


def test_ingest_argv_execroot_is_string():
    """execroot_override stored as string, not Path."""
    ingest_argv(["--execroot", "/some/path"])

    assert isinstance(cli_state.g["execroot_override"], str)


# =============================================================================
# interpret_arguments tests - semantic interpretation
# =============================================================================

# --- No command ---

def test_interpret_no_positionals():
    """No positional args sets command to empty string."""
    ingest_argv([])
    interpret_arguments()

    assert cli_state.g["command"] == ""


# --- User commands ---

def test_interpret_user_command():
    """Single positional becomes command."""
    ingest_argv(["build"])
    interpret_arguments()

    assert cli_state.g["command"] == "build"


def test_interpret_user_command_rejects_extra_positional():
    """User command with extra positional raises."""
    ingest_argv(["build", "extra"])

    with pytest.raises(ValueError, match="does not accept positional"):
        interpret_arguments()


# --- set command ---

def test_interpret_set_command():
    """set <key> <value> parses correctly."""
    ingest_argv(["set", "path.output", "/tmp/out"])
    interpret_arguments()

    assert cli_state.g["command"] == "set"
    assert cli_state.g["key"] == "path.output"
    assert cli_state.g["value"] == "/tmp/out"


def test_interpret_set_missing_value():
    """set <key> without value raises."""
    ingest_argv(["set", "path.output"])

    with pytest.raises(ValueError, match="set command requires exactly 2 arguments"):
        interpret_arguments()


def test_interpret_set_missing_key_and_value():
    """Bare set raises."""
    ingest_argv(["set"])

    with pytest.raises(ValueError, match="set command requires exactly 2 arguments"):
        interpret_arguments()


def test_interpret_set_too_many_args():
    """set with extra args raises."""
    ingest_argv(["set", "key", "value", "extra"])

    with pytest.raises(ValueError, match="set command requires exactly 2 arguments"):
        interpret_arguments()


# --- get command ---

def test_interpret_get_command():
    """get <key> parses correctly."""
    ingest_argv(["get", "path.output"])
    interpret_arguments()

    assert cli_state.g["command"] == "get"
    assert cli_state.g["key"] == "path.output"


def test_interpret_get_missing_key():
    """Bare get raises."""
    ingest_argv(["get"])

    with pytest.raises(ValueError, match="get command requires exactly 1 argument"):
        interpret_arguments()


def test_interpret_get_too_many_args():
    """get with extra args raises."""
    ingest_argv(["get", "key", "extra"])

    with pytest.raises(ValueError, match="get command requires exactly 1 argument"):
        interpret_arguments()


# --- help command ---

def test_interpret_help_with_command():
    """help <command> parses correctly."""
    ingest_argv(["help", "build"])
    interpret_arguments()

    assert cli_state.g["command"] == "help"
    assert cli_state.g["command_help"] == "build"


def test_interpret_help_bare():
    """Bare help is allowed (command_help stays None)."""
    ingest_argv(["help"])
    interpret_arguments()

    assert cli_state.g["command"] == "help"
    assert cli_state.g["command_help"] is None


def test_interpret_help_too_many_args():
    """help with extra args raises."""
    ingest_argv(["help", "build", "extra"])

    with pytest.raises(ValueError, match="help command accepts at most 1 argument"):
        interpret_arguments()


# =============================================================================
# Full parsing (ingest + interpret) convenience tests
# =============================================================================

def parse(argv):
    """Helper: run both parsing phases."""
    ingest_argv(argv)
    interpret_arguments()


def test_full_parse_command_with_options():
    """Command and options parse together."""
    parse(["build", "--execroot", "/project"])

    assert cli_state.g["command"] == "build"
    assert cli_state.g["execroot_override"] == "/project"


def test_full_parse_set_with_options():
    """set command with options parses correctly."""
    parse(["set", "path.out", "/tmp", "--options-file", "opts.json"])

    assert cli_state.g["command"] == "set"
    assert cli_state.g["key"] == "path.out"
    assert cli_state.g["value"] == "/tmp"
    assert cli_state.g["options_file"] == "opts.json"


def test_full_parse_options_interspersed():
    """Options can appear anywhere among positionals."""
    parse(["--execroot", "/proj", "set", "--options-file", "o.json", "key", "val"])

    assert cli_state.g["command"] == "set"
    assert cli_state.g["key"] == "key"
    assert cli_state.g["value"] == "val"
    assert cli_state.g["execroot_override"] == "/proj"
    assert cli_state.g["options_file"] == "o.json"
