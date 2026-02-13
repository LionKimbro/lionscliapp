"""Tests for lionscliapp.json_io module."""

import json
import pytest

import lionscliapp as app
from lionscliapp import declarations
from lionscliapp.json_io import read_json, write_json


def setup_function():
    """Reset all state before each test."""
    app.reset()


# =============================================================================
# read_json tests
# =============================================================================

def test_read_json_basic(tmp_path, monkeypatch):
    """read_json reads and parses a JSON file."""
    monkeypatch.chdir(tmp_path)

    # Create test file
    data_file = tmp_path / "data.json"
    data_file.write_text('{"name": "test", "count": 42}')

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.mydata", str(data_file))

    _simulate_startup(tmp_path)

    result = read_json("mydata")

    assert result == {"name": "test", "count": 42}


def test_read_json_list(tmp_path, monkeypatch):
    """read_json handles JSON arrays."""
    monkeypatch.chdir(tmp_path)

    data_file = tmp_path / "items.json"
    data_file.write_text('[1, 2, 3, "four"]')

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.items", str(data_file))

    _simulate_startup(tmp_path)

    result = read_json("items")

    assert result == [1, 2, 3, "four"]


def test_read_json_missing_path_key(tmp_path, monkeypatch):
    """read_json raises KeyError if path.<fileid> not declared."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(KeyError, match="No path configured"):
        read_json("nonexistent")


def test_read_json_file_not_found(tmp_path, monkeypatch):
    """read_json raises FileNotFoundError if file doesn't exist."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.missing", str(tmp_path / "missing.json"))

    _simulate_startup(tmp_path)

    with pytest.raises(FileNotFoundError):
        read_json("missing")


def test_read_json_invalid_json(tmp_path, monkeypatch):
    """read_json raises JSONDecodeError for invalid JSON."""
    monkeypatch.chdir(tmp_path)

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json}")

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.bad", str(bad_file))

    _simulate_startup(tmp_path)

    with pytest.raises(json.JSONDecodeError):
        read_json("bad")


# =============================================================================
# write_json tests
# =============================================================================

def test_write_json_basic(tmp_path, monkeypatch):
    """write_json writes data to a JSON file."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.output", str(out_file))

    _simulate_startup(tmp_path)

    write_json("output", {"key": "value", "num": 123})

    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content == {"key": "value", "num": 123}


def test_write_json_pretty_default(tmp_path, monkeypatch):
    """write_json defaults to pretty formatting with indent=2."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "pretty.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))

    _simulate_startup(tmp_path)

    write_json("out", {"a": 1})

    content = out_file.read_text()
    # Should have newlines and indentation
    assert "\n" in content
    assert "  " in content  # 2-space indent


def test_write_json_compact(tmp_path, monkeypatch):
    """write_json uses compact format when configured."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "compact.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))
    declarations.declare_key("json.rendering.out", "compact")

    _simulate_startup(tmp_path)

    write_json("out", {"a": 1, "b": 2})

    content = out_file.read_text().strip()
    # Compact: no spaces after : or ,
    assert content == '{"a":1,"b":2}'


def test_write_json_custom_indent(tmp_path, monkeypatch):
    """write_json uses configured indent level."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "indented.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))
    declarations.declare_key("json.indent.out", 4)

    _simulate_startup(tmp_path)

    write_json("out", {"nested": {"value": 1}})

    content = out_file.read_text()
    # Should have 4-space indentation
    assert "    " in content


def test_write_json_creates_parent_dirs(tmp_path, monkeypatch):
    """write_json creates parent directories if needed."""
    monkeypatch.chdir(tmp_path)

    out_file = tmp_path / "deep" / "nested" / "output.json"

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.out", str(out_file))

    _simulate_startup(tmp_path)

    write_json("out", {"created": True})

    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"created": True}


def test_write_json_missing_path_key(tmp_path, monkeypatch):
    """write_json raises KeyError if path.<fileid> not declared."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")

    _simulate_startup(tmp_path)

    with pytest.raises(KeyError, match="No path configured"):
        write_json("nonexistent", {"data": 1})


# =============================================================================
# Round-trip tests
# =============================================================================

def test_write_then_read_roundtrip(tmp_path, monkeypatch):
    """Data survives write_json -> read_json round-trip."""
    monkeypatch.chdir(tmp_path)

    data_file = tmp_path / "roundtrip.json"
    original = {
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"a": {"b": "c"}}
    }

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.declare_key("path.data", str(data_file))

    _simulate_startup(tmp_path)

    write_json("data", original)
    result = read_json("data")

    assert result == original


# =============================================================================
# Export tests
# =============================================================================

def test_functions_exported_from_package():
    """read_json and write_json are accessible from main package."""
    assert app.read_json is read_json
    assert app.write_json is write_json


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
