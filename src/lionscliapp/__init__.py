"""
lionscliapp - A humane CLI application framework.

Typical import:
    import lionscliapp as app
"""

from lionscliapp import application
from lionscliapp import runtime_state

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
    # future:
    # config.reset_config_cache()
    # cli.reset_cli_state()

