"""Tests for lionscliapp.file_io module."""

import pytest
from pathlib import Path

import lionscliapp as app
from lionscliapp.file_io import (
    g,
    prepare_write,
    prepare_binarywrite,
    complete_write,
    reset_file_io,
)


def setup_function():
    """Reset all global state before each test."""
    app.reset()


def test_prepare_write_returns_open_file():
    """prepare_write() returns an open text file."""
    f = prepare_write()

    assert f is not None
    assert not f.closed
    assert f.mode == "w"

    f.close()


def test_prepare_write_sets_g_tmpfile():
    """prepare_write() sets g['tmpfile']."""
    f = prepare_write()

    assert g["tmpfile"] is f

    f.close()


def test_prepare_binarywrite_returns_open_binary_file():
    """prepare_binarywrite() returns an open binary file."""
    f = prepare_binarywrite()

    assert f is not None
    assert not f.closed
    assert f.mode == "wb"

    f.close()


def test_prepare_binarywrite_sets_g_tmpfile():
    """prepare_binarywrite() sets g['tmpfile']."""
    f = prepare_binarywrite()

    assert g["tmpfile"] is f

    f.close()


def test_complete_write_creates_file(tmp_path):
    """complete_write() creates the destination file."""
    dest = tmp_path / "output.txt"

    f = prepare_write()
    f.write("hello world")
    complete_write(dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "hello world"


def test_complete_write_overwrites_existing_file(tmp_path):
    """complete_write() overwrites existing destination."""
    dest = tmp_path / "output.txt"
    dest.write_text("old content", encoding="utf-8")

    f = prepare_write()
    f.write("new content")
    complete_write(dest)

    assert dest.read_text(encoding="utf-8") == "new content"


def test_complete_write_creates_parent_directories(tmp_path):
    """complete_write() creates parent directories if needed."""
    dest = tmp_path / "nested" / "dir" / "output.txt"

    f = prepare_write()
    f.write("content")
    complete_write(dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "content"


def test_complete_write_clears_g_tmpfile(tmp_path):
    """complete_write() sets g['tmpfile'] to None."""
    dest = tmp_path / "output.txt"

    f = prepare_write()
    f.write("content")
    complete_write(dest)

    assert g["tmpfile"] is None


def test_complete_write_raises_without_prepare():
    """complete_write() raises RuntimeError if no prepare_write() was called."""
    reset_file_io()

    with pytest.raises(RuntimeError, match="called without prior"):
        complete_write(Path("/tmp/test.txt"))


def test_complete_write_binary_roundtrip(tmp_path):
    """Binary write roundtrip works correctly."""
    dest = tmp_path / "output.bin"
    data = b"\x00\x01\x02\xff\xfe"

    f = prepare_binarywrite()
    f.write(data)
    complete_write(dest)

    assert dest.read_bytes() == data


def test_reset_file_io_clears_g():
    """reset_file_io() clears g."""
    f = prepare_write()
    f.close()

    reset_file_io()

    assert g == {}


def test_reset_file_io_cleans_up_open_tmpfile(tmp_path):
    """reset_file_io() closes and removes lingering temp file."""
    f = prepare_write()
    tmppath = f.name

    reset_file_io()

    assert g == {}
    # Temp file should be cleaned up
    assert not Path(tmppath).exists()
