"""Tests for lionscliapp.tkruntime module."""

import json
import os

import pytest

import lionscliapp as app
from lionscliapp import cli_state
from lionscliapp import declarations
from lionscliapp import tkruntime
from lionscliapp.ctx import ctx


def setup_function():
    """Reset framework state before each test."""
    app.reset()


class FakeRoot:
    """Minimal Tk-like root for scheduling and foreground tests."""

    def __init__(self, hwnd=123):
        self.hwnd = hwnd
        self.after_calls = []
        self.cancelled = []
        self.actions = []

    def winfo_id(self):
        return self.hwnd

    def after(self, ms, callback):
        self.after_calls.append((ms, callback))
        return f"after-{len(self.after_calls)}"

    def after_cancel(self, after_id):
        self.cancelled.append(after_id)

    def deiconify(self):
        self.actions.append("deiconify")

    def lift(self):
        self.actions.append("lift")

    def focus_force(self):
        self.actions.append("focus_force")


def test_prepare_current_command_summons_existing_instance(tmp_path, monkeypatch):
    """A second Tk invocation writes a summon message instead of running."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.set_flag("uses_tkinter", True)
    declarations.declare_cmd("ui", lambda: None)
    declarations.set_cmd_flag("ui", "tkinter", True)
    declarations.set_cmd_flag("ui", "single_instance", True)

    _simulate_startup(tmp_path)
    cli_state.g["command"] = "ui"

    project_dir = tmp_path / ".myapp"
    instance_path = project_dir / "instance.json"
    instance_path.write_text(
        json.dumps(
            {
                "instance_id": "owner-1",
                "command": "ui",
                "pid": os.getpid(),
                "created_at": "2026-06-24T00:00:00Z",
                "window_handle": 456,
            }
        ),
        encoding="utf-8",
    )

    result = tkruntime.prepare_current_command(["myapp", "ui"])

    assert result == "summoned"

    inbox = project_dir / "inbox"
    files = list(inbox.glob("*.json"))
    assert len(files) == 1
    message = json.loads(files[0].read_text(encoding="utf-8"))
    assert message["type"] == "summon"
    assert message["command"] == "ui"


def test_attach_tk_publishes_handle_and_consumes_generic_messages(tmp_path, monkeypatch):
    """attach_tk() schedules polling and generic inbox messages reach the handler."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.set_flag("uses_tkinter", True)
    declarations.declare_cmd("ui", lambda: None)
    declarations.set_cmd_flag("ui", "tkinter", True)
    declarations.set_cmd_flag("ui", "single_instance", True)

    _simulate_startup(tmp_path)
    cli_state.g["command"] = "ui"
    tkruntime.acquire_instance("ui")

    seen = []
    root = FakeRoot(hwnd=999)

    tkruntime.attach_tk(root, seen.append)
    assert root.after_calls[0][0] == 1000

    tkruntime.send_message({"type": "custom", "payload": {"x": 1}})
    tkruntime.send_message({"type": "summon", "payload": {"y": 2}})

    tkruntime.poll_inbox_once()

    assert sorted(message["type"] for message in seen) == ["custom", "summon"]
    assert "deiconify" in root.actions
    assert "lift" in root.actions
    assert "focus_force" in root.actions


def test_attach_tk_uses_configured_poll_interval(tmp_path, monkeypatch):
    """attach_tk() uses runtime.gui.inbox.poll_ms when declared."""
    monkeypatch.chdir(tmp_path)

    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.set_flag("uses_tkinter", True)
    declarations.declare_key("runtime.gui.inbox.poll_ms", "800")
    declarations.declare_cmd("ui", lambda: None)
    declarations.set_cmd_flag("ui", "tkinter", True)
    declarations.set_cmd_flag("ui", "single_instance", True)

    _simulate_startup(tmp_path)
    cli_state.g["command"] = "ui"
    tkruntime.acquire_instance("ui")

    root = FakeRoot()
    tkruntime.attach_tk(root)

    assert root.after_calls[0][0] == 800


def test_prepare_current_command_refuses_nonisolated_tests():
    """Tk test mode requires explicit isolation and project-dir override."""
    declarations.declare_app("myapp", "1.0")
    declarations.declare_projectdir(".myapp")
    declarations.set_flag("uses_tkinter", True)
    declarations.declare_key("runtime.tests.enabled", "false")
    declarations.declare_key("runtime.tests.isolated", "false")
    declarations.declare_cmd("ui", lambda: None)
    declarations.set_cmd_flag("ui", "tkinter", True)
    declarations.set_cmd_flag("ui", "single_instance", True)

    cli_state.g["command"] = "ui"
    ctx.clear()
    ctx["runtime.tests.enabled"] = "true"
    ctx["runtime.tests.isolated"] = "false"

    with pytest.raises(tkruntime.TkRuntimeError, match="runtime.tests.isolated"):
        tkruntime.prepare_current_command(["myapp", "ui"])


def test_build_tkintertester_flags_reads_runtime_keys():
    """build_tkintertester_flags() maps runtime.tests keys into harness flags."""
    ctx.clear()
    ctx["runtime.tests.show"] = "true"
    ctx["runtime.tests.exit"] = "true"

    assert tkruntime.build_tkintertester_flags() == "sx"


def _simulate_startup(tmp_path):
    """Simulate startup sufficiently for ctx/path-aware tests."""
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
