"""
file_io: Atomic file writing utilities.

This module provides a simple interface for writing files atomically.
The pattern is:
    1. Call prepare_write() or prepare_binarywrite() to get a temp file
    2. Write content to the returned file object
    3. Call complete_write(path) to atomically move it to the destination

Atomic writes are achieved by creating a temp file in the destination
directory (using a GUID filename) and using os.replace() for the final move.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path


g = {}


def prepare_write():
    """
    Create and return a temporary UTF-8 text file for writing.

    Side Effects:
        Sets g["tmpfile"] to the opened NamedTemporaryFile.

    Returns:
        NamedTemporaryFile: The open temporary file object in text mode.
    """
    g["tmpfile"] = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    return g["tmpfile"]


def prepare_binarywrite():
    """
    Create and return a temporary binary file for writing.

    Side Effects:
        Sets g["tmpfile"] to the opened NamedTemporaryFile.

    Returns:
        NamedTemporaryFile: The open temporary file object in binary mode.
    """
    g["tmpfile"] = tempfile.NamedTemporaryFile(delete=False, mode="wb")
    return g["tmpfile"]


def complete_write(p):
    """
    Close the active temp file and move it to the path `p`.

    The destination is overwritten if it exists. For atomicity, the content
    is first copied to a GUID-named temp file in the destination directory,
    then os.replace() performs the atomic rename.

    Args:
        p (Path): Destination path for the completed temp file.

    Raises:
        RuntimeError: If no temp file was prepared via prepare_write() or
            prepare_binarywrite().
    """
    assert isinstance(p, Path)

    if "tmpfile" not in g or g["tmpfile"] is None:
        raise RuntimeError("complete_write() called without prior prepare_write() or prepare_binarywrite()")

    tmpfile = g["tmpfile"]
    tmpfile.close()
    source_path = tmpfile.name

    p.parent.mkdir(parents=True, exist_ok=True)
    dest_tmp = p.parent / f".tmp_{uuid.uuid4().hex}"

    try:
        shutil.copy2(source_path, dest_tmp)
        os.replace(dest_tmp, p)
    except Exception as e:
        print(f"ERROR: Failed to write file to {p}")
        print(f"Intended destination: {p}")
        print(f"Temp file was: {source_path}")
        try:
            with open(source_path, "r", encoding="utf-8", errors="replace") as f:
                print("Contents:")
                print(f.read())
        except Exception:
            print("(Could not read temp file contents)")
        if dest_tmp.exists():
            os.unlink(dest_tmp)
        raise
    finally:
        if os.path.exists(source_path):
            os.unlink(source_path)
        g["tmpfile"] = None


def reset_file_io():
    """
    Reset file_io state (used for tests).

    Cleans up any lingering temp file and clears g.
    """
    if "tmpfile" in g and g["tmpfile"] is not None:
        try:
            g["tmpfile"].close()
        except Exception:
            pass
        try:
            os.unlink(g["tmpfile"].name)
        except Exception:
            pass
    g.clear()
