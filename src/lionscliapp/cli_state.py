
# cli_state.py

g = {
    "command": None,              # None | str
    "options_file": None,         # None | str (path)
    "execroot_override": None,    # None | str (path)
}

option_overrides = {}  # dict[str, str]


def reset_cli_state():
    g["command"] = None
    g["options_file"] = None
    g["execroot_override"] = None
    option_overrides.clear()
