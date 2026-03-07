# lionscliapp

**A framework for building small command-line tools that remember things.**

`lionscliapp` is a humane CLI application framework for Python. It makes it easy to build stateful developer tools quickly — tools that have persistent configuration, multiple sub-commands, and native support for paths and JSON files, without any argument-parsing boilerplate.

## What It Provides

- **Persistence** — Each project gets a hidden directory (e.g. `.mytool/`) with a `config.json`. Users set values once; the tool remembers them.
- **Automatic CLI parsing** — Declare keys; the framework parses, persists, and merges values into `app.ctx`. No argparser to write.
- **Multiple commands** — Bind as many sub-commands as you like, or declare a default handler for bare invocations.
- **Paths are native** — Any key prefixed with `path.` becomes a `pathlib.Path`, expanded and resolved automatically.
- **JSON is native** — `read_json()` and `write_json()` handle path resolution and formatting. Reading or writing a named JSON file is a one-liner.
- **Built-in commands** — `set`, `get`, `keys`, and `help` are always available for free.

## What It Doesn't Do

`lionscliapp` is deliberately simple. Configuration values are strings (except `path.*` keys, which become `pathlib.Path`). There is no built-in type system for integers, booleans, or enums — coerce from `app.ctx` yourself if you need them. This is a trade-off in favour of a smaller mental model.

## Installation

Requires Python 3.10+.

```bash
pip install -e .
```

## Quick Start

```python
import lionscliapp as app

app.declare_app("mytool", "1.0")
app.describe_app("A tool that does useful things")

app.declare_projectdir(".mytool")

app.declare_key("path.output", "~/output")
app.declare_key("path.input",  "~/input")

def cmd_run():
    output = app.ctx["path.output"]  # pathlib.Path, fully resolved
    print(f"Output will go to: {output}")

app.declare_cmd("run", cmd_run)
app.describe_cmd("run", "Run the main process")

app.main()
```

```bash
mytool run                          # uses defaults
mytool set path.output ~/my-output  # persist a value
mytool --path.output /tmp run       # override for this invocation only
mytool help
mytool keys
```

## Status

**Version:** 0.1.2 (v0 specification)

Core framework is complete: lifecycle management, command dispatch, built-in commands, configuration layering and persistence, path coercion, JSON I/O utilities.

## License

See LICENSE file for details.

---

📖 **[Full Reference Guide](doc/reference.md)**
