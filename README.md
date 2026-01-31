# lionscliapp

A humane CLI application framework for Python.

`lionscliapp` removes the argument-parsing tax from CLI tool development while providing persistent per-project configuration, typed option namespaces, and a clean execution model. It emphasizes inspectability, clarity, and long-lived tooling.

## Features

- **Declarative Application Structure** — Declare commands, options, and descriptions through a simple API
- **Persistent Per-Project Configuration** — Each project maintains a `.json` config file that survives across invocations
- **Configuration Layering** — Values merge from defaults → disk config → options file → CLI overrides
- **Namespace-Based Type Coercion** — Automatic conversion based on key prefixes:
  - `path.*` → `pathlib.Path`
  - `json.rendering.*` → enum (`"pretty"`, `"compact"`)
  - `json.indent.*` → integer ≥ 0
- **Built-in Commands** — `set`, `get`, and `help` provided out of the box
- **Two-Phase CLI Parsing** — Framework options parsed separately from command arguments
- **JSON as Universal Substrate** — All declarative data is JSON-serializable

## Installation

Requires Python 3.10+.

```bash
pip install -e .
```

## Quick Start

```python
import lionscliapp as app

# Declare app identity
app.declare_app("mytool", "1.0")
app.describe_app("A tool that does useful things")

# Declare project directory for persistent config
app.declare_projectdir(".mytool")

# Declare configuration keys with defaults
app.declare_key("path.output", "/tmp/output")
app.declare_key("json.indent.data", 2)

# Define and bind commands
def run_command():
    output_path = app.ctx["path.output"]  # Already a pathlib.Path
    print(f"Output will go to: {output_path}")

app.declare_cmd("run", run_command)
app.describe_cmd("run", "Run the main process")

# Start the application
app.main()
```

## CLI Usage

```bash
# Show help
mytool help

# Run a user-defined command
mytool run

# Set a persistent config value
mytool set path.output /new/path

# Get a config value
mytool get path.output

# Override options via CLI (transient)
mytool --path.output /tmp run

# Load overrides from a JSON file
mytool --options-file overrides.json run

# Override execution root
mytool --execroot /other/project run
```

## Project Structure

```
src/lionscliapp/
├── __init__.py        # Public API exports
├── application.py     # Application data model
├── declarations.py    # Declaration API (declare_app, declare_cmd, etc.)
├── entrypoint.py      # Main entry point and lifecycle
├── dispatch.py        # Command dispatch
├── builtins.py        # Built-in commands (set, get, help)
├── ctx.py             # Runtime context construction
├── cli_parsing.py     # Two-phase CLI parsing
├── config_io.py       # Config file I/O
├── execroot.py        # Execution root resolution
└── ...
```

## Status

**Version:** 0.1.0 (v0 specification)

Core framework is complete with:
- Full lifecycle management
- Command dispatch with exit codes
- Built-in commands
- Configuration layering and persistence
- Type coercion

Future plans include programmatic invocation (`app.run()`), interactive config editing, and extensible namespace registration.

## License

See LICENSE file for details.
