"""
tkruntime: Optional Tkinter single-instance and FileTalk mailbox support.

This subsystem is separate from generic command locking. It is intended for
GUI commands where a second invocation should usually summon an existing
instance instead of failing.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from lionscliapp import application as appmodel
from lionscliapp import cli_state
from lionscliapp import override_inputs
from lionscliapp.ctx import ctx
from lionscliapp.paths import get_inbox_path, get_instance_path


DEFAULT_POLL_MS = 1000
DEFAULT_HANDLER_FLAGS = {
    "summon": True,
}

_state = {
    "instance": None,
    "root": None,
    "message_handler": None,
    "poll_after_id": None,
    "current_command": None,
}


class TkRuntimeError(Exception):
    """Raised when Tkinter runtime ownership or mailbox behavior fails."""
    pass


def reset_tk_runtime():
    """Reset all Tk runtime state in place."""
    _state["instance"] = None
    _state["root"] = None
    _state["message_handler"] = None
    _state["poll_after_id"] = None
    _state["current_command"] = None


def uses_tkinter() -> bool:
    """Return True when the application has opted into Tk runtime support."""
    return appmodel.application["flags"].get("uses_tkinter", False)


def command_uses_tkinter(command: str) -> bool:
    """Return True when a command is marked as a Tk command."""
    if not uses_tkinter():
        return False

    schema = appmodel.application["commands"].get(command)
    if schema is None:
        return False
    return schema.get("flags", {}).get("tkinter", False)


def command_is_single_instance(command: str) -> bool:
    """Return True when a Tk command should summon instead of launching twice."""
    if not command_uses_tkinter(command):
        return False

    schema = appmodel.application["commands"].get(command)
    return schema.get("flags", {}).get("single_instance", False)


def prepare_current_command(argv: list[str]) -> str:
    """
    Prepare the current Tk command before dispatch.

    Returns:
        "run" when the command should execute normally
        "summoned" when an existing instance was notified instead

    Raises:
        TkRuntimeError: On stale test-safety or ownership errors.
    """
    command = cli_state.g["command"]
    if command is None:
        command = ""

    _state["current_command"] = command

    if not command_uses_tkinter(command):
        return "run"

    _validate_test_mode_safety()

    if not command_is_single_instance(command):
        return "run"

    owner = read_instance_file()
    if owner is not None and _instance_payload_is_live(owner):
        send_message(_build_summon_message(argv))
        return "summoned"

    if owner is not None:
        remove_stale_instance_file()

    acquire_instance(command)
    return "run"


def acquire_instance(command: str):
    """Acquire instance.json using exclusive creation semantics."""
    instance_path = get_instance_path()
    payload = {
        "instance_id": str(uuid.uuid4()),
        "command": command,
        "pid": os.getpid(),
        "created_at": _utc_now_text(),
        "window_handle": None,
    }

    try:
        with instance_path.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
    except FileExistsError as e:
        existing = read_instance_file()
        raise TkRuntimeError(_format_existing_instance_message(instance_path, existing)) from e

    _state["instance"] = payload
    return payload


def release_instance():
    """Release the current instance.json file if still owned by this execution."""
    instance = _state["instance"]
    if instance is None:
        return

    path = get_instance_path()
    try:
        payload = _read_json_file(path)
    except FileNotFoundError:
        _state["instance"] = None
        return

    if payload.get("instance_id") != instance.get("instance_id"):
        raise TkRuntimeError(
            "Refusing to remove instance.json because ownership changed. "
            f"Current instance_id={payload.get('instance_id')!r}, "
            f"expected {instance.get('instance_id')!r}."
        )

    path.unlink()
    _state["instance"] = None


def attach_tk(root, message_handler=None):
    """
    Attach the Tk runtime to a live root-like object.

    This schedules recurring FileTalk mailbox polling on the Tk event loop.
    """
    _state["root"] = root
    _state["message_handler"] = message_handler

    _schedule_next_poll()


def detach_tk():
    """Detach the Tk runtime from the live root and stop future polling."""
    root = _state["root"]
    after_id = _state["poll_after_id"]

    if root is not None and after_id is not None and hasattr(root, "after_cancel"):
        try:
            root.after_cancel(after_id)
        except Exception:
            pass

    _state["root"] = None
    _state["message_handler"] = None
    _state["poll_after_id"] = None


def publish_instance_metadata(updates: dict):
    """Merge metadata into the owned instance.json file."""
    instance = _state["instance"]
    if instance is None:
        raise TkRuntimeError("No owned Tk instance is active for metadata publication.")

    path = get_instance_path()
    payload = _read_json_file(path)
    if payload.get("instance_id") != instance.get("instance_id"):
        raise TkRuntimeError("Cannot publish metadata: instance ownership changed.")

    payload.update(updates)
    _write_json_atomic(path, payload)
    instance.update(updates)


def send_message(message: dict) -> Path:
    """
    Write a generic FileTalk-style message into inbox/.

    The message must be JSON-serializable and should typically include
    envelope fields such as type/id/created.
    """
    if not isinstance(message, dict):
        raise TkRuntimeError(
            f"Mailbox messages must be JSON dictionaries, got {type(message).__name__!r}"
        )

    inbox = get_inbox_path()
    inbox.mkdir(parents=True, exist_ok=True)

    message_id = message.get("id") or str(uuid.uuid4())
    path = inbox / f"{message_id}.json"

    payload = dict(message)
    payload["id"] = message_id

    try:
        with path.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
    except FileExistsError:
        path = inbox / f"{message_id}-{uuid.uuid4()}.json"
        with path.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")

    return path


def consume_messages() -> list[dict]:
    """
    Read and delete complete JSON messages from inbox/.

    Files that are incomplete or invalid JSON are left in place so they can
    be retried on a later poll.
    """
    inbox = get_inbox_path()
    if not inbox.exists():
        return []

    messages = []
    for path in sorted(inbox.glob("*.json")):
        try:
            payload = _read_json_file(path)
        except (json.JSONDecodeError, OSError, TkRuntimeError):
            continue

        messages.append(payload)
        path.unlink()

    return messages


def poll_inbox_once():
    """Consume inbox messages once and dispatch them to the handler/root."""
    messages = consume_messages()
    if not messages:
        return

    root = _state["root"]
    handler = _state["message_handler"]

    for message in messages:
        if message.get("type") == "summon" and root is not None:
            bring_window_to_front(root)
        if handler is not None:
            handler(message)


def bring_window_to_front(root):
    """Bring a Tk-like root to the foreground as best we can."""
    if hasattr(root, "deiconify"):
        root.deiconify()
    if hasattr(root, "lift"):
        root.lift()
    if hasattr(root, "focus_force"):
        try:
            root.focus_force()
        except Exception:
            pass

def build_tkintertester_flags() -> str:
    """
    Build tkintertester harness flags from runtime.tests.* configuration.

    This does not import tkintertester; it just translates the standard
    lionscliapp runtime keys into the harness's flag vocabulary.
    """
    flags = ""
    if _ctx_flag_enabled("runtime.tests.show", False):
        flags += "s"
    if _ctx_flag_enabled("runtime.tests.exit", False):
        flags += "x"
    return flags


def tests_enabled() -> bool:
    """Return True when runtime.tests.enabled is configured truthy."""
    return _ctx_flag_enabled("runtime.tests.enabled", False)


def read_instance_file():
    """Return the current instance payload, or None if no owner exists."""
    path = get_instance_path()
    try:
        return _read_json_file(path)
    except FileNotFoundError:
        return None


def remove_stale_instance_file():
    """Remove instance.json when its owning PID is no longer alive."""
    payload = read_instance_file()
    if payload is None:
        return None

    if _instance_payload_is_live(payload):
        return payload

    get_instance_path().unlink()
    return payload


def _schedule_next_poll():
    """Schedule the next inbox poll on the Tk event loop."""
    root = _state["root"]
    if root is None or not hasattr(root, "after"):
        return

    ms = _get_poll_interval_ms()
    _state["poll_after_id"] = root.after(ms, _poll_callback)


def _poll_callback():
    """Tk event-loop callback for mailbox polling."""
    try:
        poll_inbox_once()
    finally:
        _schedule_next_poll()


def _get_poll_interval_ms() -> int:
    """Return configured inbox poll interval in milliseconds."""
    raw = ctx.get("runtime.gui.inbox.poll_ms")
    if raw is None:
        return DEFAULT_POLL_MS

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise TkRuntimeError(
            f"runtime.gui.inbox.poll_ms must be an integer, got {raw!r}"
        )

    if value <= 0:
        raise TkRuntimeError(
            f"runtime.gui.inbox.poll_ms must be > 0, got {value!r}"
        )

    return value


def _ctx_flag_enabled(key: str, default: bool) -> bool:
    """Interpret a ctx value as a boolean flag without changing ctx semantics."""
    raw = ctx.get(key)
    if raw is None:
        return default

    if isinstance(raw, bool):
        return raw

    if isinstance(raw, str):
        text = raw.strip().lower()
        if text in ("1", "true", "yes", "y", "on"):
            return True
        if text in ("0", "false", "no", "n", "off", ""):
            return False

    raise TkRuntimeError(f"{key} must be a boolean-like value, got {raw!r}")


def _validate_test_mode_safety():
    """Refuse Tk test runs that are not explicitly isolated."""
    if not tests_enabled():
        return

    if not _ctx_flag_enabled("runtime.tests.isolated", False):
        raise TkRuntimeError(
            "runtime.tests.enabled is true for a Tk command, but "
            "runtime.tests.isolated is not true. Refusing to run tests "
            "against a potentially live data environment."
        )

    if cli_state.g["project_dir_override"] is None:
        raise TkRuntimeError(
            "runtime.tests.enabled is true for a Tk command, but no "
            "--project-dir override was provided. Refusing to run tests "
            "without an isolated project directory."
        )


def _instance_payload_is_live(payload: dict) -> bool:
    """Return True when the payload appears to describe a live process."""
    pid = payload.get("pid")
    return _pid_is_alive(pid)


def _pid_is_alive(pid) -> bool:
    """Return True if the given PID appears to be alive."""
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False

    if pid_int <= 0:
        return False

    if pid_int == os.getpid():
        return True

    try:
        os.kill(pid_int, 0)
        return True
    except OSError:
        return False


def _build_summon_message(argv: list[str]) -> dict:
    """Build the default summon message for a second invocation."""
    return {
        "lionscliapp-message": "1",
        "id": str(uuid.uuid4()),
        "type": "summon",
        "created": _utc_now_text(),
        "sender-pid": os.getpid(),
        "command": _state["current_command"],
        "argv": list(argv),
        "cli-overrides": dict(override_inputs.cli_overrides),
    }


def _format_existing_instance_message(path, payload):
    """Build a readable message about an already-running instance."""
    if payload is None:
        return f"Tk instance already active: {path}"

    return (
        f"Tk instance already active: {path}\n"
        f"  command: {payload.get('command')!r}\n"
        f"  pid: {payload.get('pid')!r}\n"
        f"  created_at: {payload.get('created_at')!r}"
    )


def _utc_now_text():
    """Return the current UTC timestamp in ISO-8601 text form."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json_file(path: Path):
    """Read a JSON object from disk."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TkRuntimeError(f"Expected JSON object in {path}")
    return data


def _write_json_atomic(path: Path, data: dict):
    """Atomically replace a JSON file on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    temp_path.replace(path)
