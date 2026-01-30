"""
lionscliapp - A humane CLI application framework.

Typical import:
    import lionscliapp as app
"""

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

