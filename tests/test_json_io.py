"""Tests for lionscliapp.json_io module."""

import json
import pytest

import lionscliapp as app
from lionscliapp import declarations
from lionscliapp.json_io import read_json, write_json, DEFAULT_INDENT
from lionscliapp.paths import get_path


def setup_function():
    """Reset all state before each test."""
    app.reset()


# =============================================================================
# get_path tests
# =============================================================================

def test_get_path_configured(tmp_path, monkeypatch):
    """get_path with 'c' mode resolves from ctx."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.myfile", str(tmp_path / "data.json"))

    _simulate_startup(tmp_path)

    result = get_path("myfile", "c")
    assert result == tmp_path / "data.json"


def test_get_path_configured_missing_key(tmp_path, monkeypatch):
    """get_path with 'c' mode raises KeyError if not declared."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(KeyError, match="No path configured"):
        get_path("missing", "c")


def test_get_path_project(tmp_path, monkeypatch):
    """get_path with 'p' mode resolves relative to project root."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    result = get_path("state.json", "p")
    assert result == tmp_path / ".myapp" / "state.json"


def test_get_path_project_absolute(tmp_path, monkeypatch):
    """get_path with 'p' mode returns absolute path unchanged."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    abs_path = tmp_path / "elsewhere" / "file.json"
    result = get_path(str(abs_path), "p")
    assert result == abs_path


def test_get_path_execroot(tmp_path, monkeypatch):
    """get_path with 'e' mode resolves relative to execution root."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    result = get_path("output.json", "e")
    assert result == tmp_path / "output.json"


def test_get_path_filesystem(tmp_path, monkeypatch):
    """get_path with 'f' mode resolves relative to cwd."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    result = get_path("relative.json", "f")
    assert result == tmp_path / "relative.json"


def test_get_path_invalid_mode(tmp_path, monkeypatch):
    """get_path raises ValueError for invalid mode."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="Invalid path mode"):
        get_path("file", "x")


# =============================================================================
# read_json tests
# =============================================================================

def test_read_json_configured(tmp_path, monkeypatch):
    """read_json with 'c' mode reads from configured path."""
    monkeypatch.chdir(tmp_path)

    data_file = tmp_path / "data.json"
    data_file.write_text('{"key": "value"}')

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.mydata", str(data_file))

    _simulate_startup(tmp_path)

    result = read_json("mydata", "c")
    assert result == {"key": "value"}


def test_read_json_default_mode(tmp_path, monkeypatch):
    """read_json defaults to 'c' mode."""
    monkeypatch.chdir(tmp_path)

    data_file = tmp_path / "data.json"
    data_file.write_text('{"default": true}')

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.mydata", str(data_file))

    _simulate_startup(tmp_path)

    result = read_json("mydata")  # no mode specified
    assert result == {"default": True}


def test_read_json_project(tmp_path, monkeypatch):
    """read_json with 'p' mode reads from project directory."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    # Create file in project directory
    project_file = tmp_path / ".myapp" / "state.json"
    project_file.write_text('{"from": "project"}')

    result = read_json("state.json", "p")
    assert result == {"from": "project"}


def test_read_json_execroot(tmp_path, monkeypatch):
    """read_json with 'e' mode reads from execution root."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    # Create file in execroot
    exec_file = tmp_path / "data.json"
    exec_file.write_text('{"from": "execroot"}')

    result = read_json("data.json", "e")
    assert result == {"from": "execroot"}


def test_read_json_filesystem(tmp_path, monkeypatch):
    """read_json with 'f' mode reads literal path."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    # Create file
    fs_file = tmp_path / "literal.json"
    fs_file.write_text('{"from": "filesystem"}')

    result = read_json(str(fs_file), "f")
    assert result == {"from": "filesystem"}


def test_read_json_rejects_format_flag(tmp_path, monkeypatch):
    """read_json raises ValueError if format flag present."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="Format flags not allowed"):
        read_json("file.json", "p2")


def test_read_json_file_not_found(tmp_path, monkeypatch):
    """read_json raises FileNotFoundError for missing file."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(FileNotFoundError):
        read_json("missing.json", "p")


# =============================================================================
# write_json tests - path modes
# =============================================================================

def test_write_json_configured(tmp_path, monkeypatch):
    """write_json with 'c' mode writes to configured path."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))

    _simulate_startup(tmp_path)

    write_json("out", {"key": "value"}, "c")

    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"key": "value"}


def test_write_json_default_mode(tmp_path, monkeypatch):
    """write_json defaults to 'c' mode."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))

    _simulate_startup(tmp_path)

    write_json("out", {"default": True})  # no mode

    assert json.loads(out_file.read_text()) == {"default": True}


def test_write_json_project(tmp_path, monkeypatch):
    """write_json with 'p' mode writes to project directory."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("state.json", {"state": 1}, "p")

    project_file = tmp_path / ".myapp" / "state.json"
    assert project_file.exists()
    assert json.loads(project_file.read_text()) == {"state": 1}


def test_write_json_execroot(tmp_path, monkeypatch):
    """write_json with 'e' mode writes to execution root."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("output.json", {"exec": True}, "e")

    exec_file = tmp_path / "output.json"
    assert exec_file.exists()
    assert json.loads(exec_file.read_text()) == {"exec": True}


def test_write_json_filesystem(tmp_path, monkeypatch):
    """write_json with 'f' mode writes to literal path."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    out_path = tmp_path / "literal.json"
    write_json(str(out_path), {"literal": True}, "f")

    assert out_path.exists()
    assert json.loads(out_path.read_text()) == {"literal": True}


def test_write_json_creates_parent_dirs(tmp_path, monkeypatch):
    """write_json creates parent directories."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("deep/nested/file.json", {"nested": True}, "p")

    nested_file = tmp_path / ".myapp" / "deep" / "nested" / "file.json"
    assert nested_file.exists()


# =============================================================================
# write_json tests - format flags
# =============================================================================

def test_write_json_compact_flag(tmp_path, monkeypatch):
    """write_json with '0' flag writes compact JSON."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("out.json", {"a": 1, "b": 2}, "p0")

    content = (tmp_path / ".myapp" / "out.json").read_text().strip()
    assert content == '{"a":1,"b":2}'


def test_write_json_pretty_flag(tmp_path, monkeypatch):
    """write_json with '2' flag writes indented JSON."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("out.json", {"a": 1}, "p2")

    content = (tmp_path / ".myapp" / "out.json").read_text()
    assert "\n" in content
    assert "  " in content  # 2-space indent


def test_write_json_flag_order_independent(tmp_path, monkeypatch):
    """Mode flags can be in any order."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    # "0p" should work same as "p0"
    write_json("out.json", {"a": 1}, "0p")

    content = (tmp_path / ".myapp" / "out.json").read_text().strip()
    assert content == '{"a":1}'


# =============================================================================
# write_json tests - configured formatting from ctx
# =============================================================================

def test_write_json_configured_uses_ctx_rendering(tmp_path, monkeypatch):
    """'c' mode without format flag uses compact when json.indent.<id>=0."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))
    declarations.declare_key("json.indent.out", 0)

    _simulate_startup(tmp_path)

    write_json("out", {"a": 1, "b": 2}, "c")

    content = out_file.read_text().strip()
    assert content == '{"a":1,"b":2}'


def test_write_json_configured_uses_ctx_indent(tmp_path, monkeypatch):
    """'c' mode without format flag honors json.indent.<id> from ctx."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))
    declarations.declare_key("json.indent.out", 4)

    _simulate_startup(tmp_path)

    write_json("out", {"nested": {"value": 1}}, "c")

    content = out_file.read_text()
    assert "    " in content  # 4-space indent


def test_write_json_format_flag_overrides_ctx(tmp_path, monkeypatch):
    """Explicit format flag overrides ctx settings."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))
    declarations.declare_key("json.indent.out", 0)  # would be compact

    _simulate_startup(tmp_path)

    write_json("out", {"a": 1}, "c2")  # but we force indent=2

    content = out_file.read_text()
    assert "\n" in content  # not compact


def test_write_json_non_configured_ignores_ctx(tmp_path, monkeypatch):
    """Non-'c' modes don't check ctx for formatting."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    # Declare ctx keys that would apply if using 'c' mode
    declarations.declare_key("json.indent.state", 0)

    _simulate_startup(tmp_path)

    # Using 'p' mode, so ctx settings are ignored
    write_json("state.json", {"a": 1}, "p")

    content = (tmp_path / ".myapp" / "state.json").read_text()
    # Should use default (indent=2), not compact
    assert "\n" in content


# =============================================================================
# Mode parsing error tests
# =============================================================================

def test_mode_empty_raises(tmp_path, monkeypatch):
    """Empty mode raises ValueError."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="cannot be empty"):
        write_json("file.json", {}, "")


def test_mode_no_path_flag_raises(tmp_path, monkeypatch):
    """Mode without path flag raises ValueError."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="exactly one path flag"):
        write_json("file.json", {}, "2")


def test_mode_multiple_path_flags_raises(tmp_path, monkeypatch):
    """Multiple path flags raises ValueError."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="Multiple path flags"):
        write_json("file.json", {}, "pe")


def test_mode_multiple_format_flags_raises(tmp_path, monkeypatch):
    """Multiple format flags raises ValueError."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="Multiple format flags"):
        write_json("file.json", {}, "p02")


def test_mode_unknown_flag_raises(tmp_path, monkeypatch):
    """Unknown flag raises ValueError."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(ValueError, match="Unknown flag"):
        write_json("file.json", {}, "px")


# =============================================================================
# Round-trip test
# =============================================================================

def test_write_then_read_roundtrip(tmp_path, monkeypatch):
    """Data survives write_json -> read_json round-trip."""
    monkeypatch.chdir(tmp_path)

    original = {
        "string": "hello",
        "number": 42,
        "nested": {"a": {"b": "c"}}
    }

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    write_json("data.json", original, "p")
    result = read_json("data.json", "p")

    assert result == original


# =============================================================================
# Export tests
# =============================================================================

def test_functions_exported():
    """Functions are accessible from main package."""
    assert app.read_json is read_json
    assert app.write_json is write_json
    assert app.get_path is get_path


# =============================================================================
# Helpers
# =============================================================================

def _simulate_startup(tmp_path):
    """Simulate the startup sequence for testing."""
    from lionscliapp import runtime_state
    from lionscliapp import execroot
    from lionscliapp import config_io
    from lionscliapp.paths import ensure_project_root_exists
    from lionscliapp.ctx import build_ctx

    runtime_state.transition_to_running()
    execroot.set_execroot(tmp_path)
    ensure_project_root_exists()
    config_io.load_config()
    build_ctx()
