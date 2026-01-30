"""
lionscliapp - A humane CLI application framework.

Typical import:
    import lionscliapp as app
"""

from lionscliapp import application
from lionscliapp import runtime_state
from lionscliapp import execroot
from lionscliapp import file_io
from lionscliapp import config_io
from lionscliapp import cli_state
from lionscliapp import ctx as ctx_module

from lionscliapp.ctx import ctx

from lionscliapp.runtime_state import get_phase
from lionscliapp.entrypoint import main
from lionscliapp.declarations import (
    declare_app,
    describe_app,
    declare_projectdir,
    declare_cmd,
    describe_cmd,
    declare_key,
    describe_key,
    declare,
)


def reset():
    """
    Reset all global framework state to the initial declaring-ready state.

    Intended for tests, REPL use, and controlled development workflows.
    This function forcefully resets state without lifecycle checks.
    """
    application.reset_application()
    runtime_state.reset_runtime_state()
    execroot.reset_execroot()
    file_io.reset_file_io()
    config_io.reset_config()
    cli_state.reset_cli_state()
    ctx_module.reset_ctx()

