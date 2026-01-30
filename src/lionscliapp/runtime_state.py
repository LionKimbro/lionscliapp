"""
runtime_state: Framework execution phase and mutability guard.

This module implements the data_models.runtime_state structure from the spec.
The runtime state tracks the current execution phase and enforces mutation rules.

Phases:
    declaring - Declarations are still permitted (initial state)
    running   - Application is executing; structural mutation forbidden
    shutdown  - Program is terminating

State transitions:
    declaring -> running  (triggered by entry to app.main())
    running -> shutdown   (triggered by normal or abnormal termination)

Enforcement rules:
    All declaration APIs must check that phase == 'declaring'.
    Mutation attempts when phase != 'declaring' must raise error.
"""

ALLOWED_PHASES = ("declaring", "running", "shutdown")

_state = {
    "phase": "declaring"
}


def reset_runtime_state():
    _state["phase"] = "declaring"


def get_phase():
    """Return the current execution phase."""
    return _state["phase"]


def transition_to_running():
    """
    Transition from declaring to running phase.

    Called at entry to app.main().

    Raises:
        RuntimeError: If current phase is not 'declaring'.
    """
    current = _state["phase"]
    if current != "declaring":
        raise RuntimeError(
            f"Cannot transition to 'running' phase: "
            f"current phase is '{current}', expected 'declaring'. "
            f"This transition occurs at entry to app.main()."
        )
    _state["phase"] = "running"


def transition_to_shutdown():
    """
    Transition from running to shutdown phase.

    Called on normal or abnormal termination.

    Raises:
        RuntimeError: If current phase is not 'running'.
    """
    current = _state["phase"]
    if current != "running":
        raise RuntimeError(
            f"Cannot transition to 'shutdown' phase: "
            f"current phase is '{current}', expected 'running'. "
            f"This transition occurs on program termination."
        )
    _state["phase"] = "shutdown"


def require_declaring_phase():
    """
    Guard function for declaration APIs.

    All declaration APIs must call this before making structural mutations.
    Raises a clear error if the framework is not in the declaring phase.

    Raises:
        RuntimeError: If current phase is not 'declaring'.
    """
    current = _state["phase"]
    if current != "declaring":
        raise RuntimeError(
            f"Declaration not permitted: framework is in '{current}' phase. "
            f"Structural declarations are only allowed during the 'declaring' phase, "
            f"which ends when app.main() is called."
        )


reset_runtime_state()
