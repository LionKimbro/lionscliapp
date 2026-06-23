"""
locking: Per-command lock acquisition and release.

This module implements optional project-directory locking for commands
that should not run concurrently. Locks are represented by a lock.json
file in the resolved project directory.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from lionscliapp import application as appmodel
from lionscliapp import cli_state
from lionscliapp.paths import get_lock_path


_lock_state = {
    "lock_id": None,
    "path": None,
}


class LockError(Exception):
    """Raised when a command cannot acquire or release the project lock."""
    pass


def reset_locking():
    """Reset lock-tracking state in place."""
    _lock_state["lock_id"] = None
    _lock_state["path"] = None


def uses_locking():
    """Return True when the application has opted into locking."""
    return appmodel.application["flags"].get("uses_locking", False)


def command_requires_lock(command: str) -> bool:
    """Return True when the named command is declared as lock-requiring."""
    if not uses_locking():
        return False

    commands = appmodel.application["commands"]
    if command not in commands:
        return False

    flags = commands[command].get("flags", {})
    return flags.get("locking", False)


def acquire_lock_for_current_command():
    """
    Acquire the project lock for the current command if needed.

    Raises:
        LockError: If the command requires a lock and one already exists.
    """
    command = cli_state.g["command"]
    if command is None:
        command = ""

    if not command_requires_lock(command):
        return

    lock_path = get_lock_path()
    payload = {
        "lock_id": str(uuid.uuid4()),
        "command": command,
        "pid": os.getpid(),
        "created_at": _utc_now_text(),
    }

    try:
        with lock_path.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
    except FileExistsError as e:
        existing = read_lock_file()
        raise LockError(_format_locked_message(lock_path, existing)) from e

    _lock_state["lock_id"] = payload["lock_id"]
    _lock_state["path"] = lock_path


def release_lock_for_current_command():
    """
    Release the current command's lock if it still owns it.

    Raises:
        LockError: If the lock file exists but is owned by some other lock id.
    """
    lock_id = _lock_state["lock_id"]
    lock_path = _lock_state["path"]

    if lock_id is None or lock_path is None:
        return

    try:
        payload = _read_json_file(lock_path)
    except FileNotFoundError:
        reset_locking()
        return

    if payload.get("lock_id") != lock_id:
        raise LockError(
            "Refusing to remove lock.json because it is no longer owned by "
            f"this execution. Current file lock_id={payload.get('lock_id')!r}, "
            f"expected {lock_id!r}."
        )

    lock_path.unlink()
    reset_locking()


def read_lock_file():
    """
    Read and return the current lock file payload, if present.

    Returns:
        dict | None: Lock payload, or None if lock.json does not exist.

    Raises:
        LockError: If lock.json exists but cannot be parsed as a JSON object.
    """
    lock_path = get_lock_path()
    try:
        return _read_json_file(lock_path)
    except FileNotFoundError:
        return None


def remove_lock_file():
    """
    Remove lock.json unconditionally, if present.

    Returns:
        dict | None: The prior lock payload if one existed, else None.
    """
    payload = read_lock_file()
    if payload is None:
        return None

    get_lock_path().unlink()
    if _lock_state["path"] == get_lock_path():
        reset_locking()
    return payload


def _utc_now_text():
    """Return the current UTC timestamp in ISO-8601 text form."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json_file(path):
    """Read a JSON object from the given path."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise LockError(f"Lock file must contain a JSON object: {path}")
    return data


def _format_locked_message(lock_path, payload):
    """Build a readable error message for an existing lock."""
    if payload is None:
        return f"Project is locked: {lock_path}"

    return (
        f"Project is locked: {lock_path}\n"
        f"  command: {payload.get('command')!r}\n"
        f"  pid: {payload.get('pid')!r}\n"
        f"  created_at: {payload.get('created_at')!r}\n"
        "If the prior execution crashed or the machine lost power, run "
        "'unlock' to remove the stale lock."
    )
