"""Tests for lionscliapp locking behavior."""

import json
import sys

import pytest

import lionscliapp as app


def setup_function():
    """Reset framework state before each test."""
    app.reset()


def test_locked_command_creates_and_releases_lock_file(tmp_path, monkeypatch):
    """A lock-requiring command creates lock.json during execution and removes it after."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    lock_snapshots = []

    def cmd_run():
        lock_path = tmp_path / ".myapp" / "lock.json"
        assert lock_path.exists()
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        lock_snapshots.append(payload)

    app.declare_app("myapp", "1.0")
    app.declare_projectdir(".myapp")
    app.set_flag("uses_locking", True)
    app.declare_cmd("run", cmd_run)
    app.set_cmd_flag("run", "locking", True)

    app.main()

    assert len(lock_snapshots) == 1
    assert lock_snapshots[0]["command"] == "run"
    assert isinstance(lock_snapshots[0]["pid"], int)
    assert lock_snapshots[0]["lock_id"]
    assert lock_snapshots[0]["created_at"]
    assert not (tmp_path / ".myapp" / "lock.json").exists()


def test_nonlocking_command_does_not_create_lock_file(tmp_path, monkeypatch):
    """A command without locking=True does not create lock.json."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "status"])

    def cmd_status():
        assert not (tmp_path / ".myapp" / "lock.json").exists()

    app.declare_app("myapp", "1.0")
    app.declare_projectdir(".myapp")
    app.set_flag("uses_locking", True)
    app.declare_cmd("status", cmd_status)

    app.main()

    assert not (tmp_path / ".myapp" / "lock.json").exists()


def test_locked_command_fails_when_stale_lock_exists(tmp_path, monkeypatch, capsys):
    """A lock-requiring command exits with code 1 when lock.json already exists."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    project_dir = tmp_path / ".myapp"
    project_dir.mkdir()
    lock_path = project_dir / "lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "lock_id": "stale-lock-id",
                "command": "other",
                "pid": 999,
                "created_at": "2026-06-22T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    def cmd_run():
        raise AssertionError("command should not execute while locked")

    app.declare_app("myapp", "1.0")
    app.declare_projectdir(".myapp")
    app.set_flag("uses_locking", True)
    app.declare_cmd("run", cmd_run)
    app.set_cmd_flag("run", "locking", True)

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Project is locked" in captured.err
    assert "other" in captured.err
    assert "unlock" in captured.err
    assert lock_path.exists()


def test_unlock_removes_stale_lock_file(tmp_path, monkeypatch):
    """The unlock built-in removes an existing lock.json file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "unlock"])

    project_dir = tmp_path / ".myapp"
    project_dir.mkdir()
    lock_path = project_dir / "lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "lock_id": "stale-lock-id",
                "command": "other",
                "pid": 999,
                "created_at": "2026-06-22T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    app.declare_app("myapp", "1.0")
    app.declare_projectdir(".myapp")
    app.set_flag("uses_locking", True)

    app.main()

    assert not lock_path.exists()


def test_locked_command_releases_lock_after_exception(tmp_path, monkeypatch):
    """A crashing locked command still releases its own lock file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["myapp", "run"])

    def cmd_run():
        lock_path = tmp_path / ".myapp" / "lock.json"
        assert lock_path.exists()
        raise ValueError("boom")

    app.declare_app("myapp", "1.0")
    app.declare_projectdir(".myapp")
    app.set_flag("uses_locking", True)
    app.declare_cmd("run", cmd_run)
    app.set_cmd_flag("run", "locking", True)

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert exc_info.value.code == 3
    assert not (tmp_path / ".myapp" / "lock.json").exists()
