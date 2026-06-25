# lionscliapp Reference Guide

```python
import lionscliapp as app
```

---

## Contents

- [Introduction](#introduction)
  - [What It Provides](#what-it-provides)
  - [What It Doesn't Do](#what-it-doesnt-do)
  - [Design Ethos](#design-ethos)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [A Complete Example](#a-complete-example)
- [Keys and Namespaces](#keys-and-namespaces)
  - [What a Key Is](#what-a-key-is)
  - [Values Are Strings](#values-are-strings)
  - [`path.*` — The Special Case](#path--the-special-case)
  - [`json.indent.*` — JSON Output Configuration](#jsonindent--json-output-configuration)
  - [The ctx Dictionary](#the-ctx-dictionary)
- [Configuration Layering](#configuration-layering)
  - [Config File Format](#config-file-format)
  - [Options File Format](#options-file-format)
- [Built-in Commands](#built-in-commands)
  - [`set <key> <value>`](#set-key-value)
  - [`get <key>`](#get-key)
  - [`keys`](#keys)
  - [`help [command]`](#help-command)
  - [`help-basics`](#help-basics)
- [CLI Global Options](#cli-global-options)
  - [`--<key> <value>`](#--key-value)
  - [`--options-file <path>`](#--options-file-path)
  - [`--execroot <path>`](#--execroot-path)
  - [`--project-dir <name>`](#--project-dir-name)
- [Path Resolution](#path-resolution)
- [JSON I/O](#json-io)
- [Tkinter Runtime](#tkinter-runtime)
- [Lifecycle Phases](#lifecycle-phases)
- [Complete Function Reference](#complete-function-reference)
  - [Declaration Functions](#declaration-functions)
  - [Entry Point](#entry-point)
  - [Runtime Context](#runtime-context)
  - [Path and JSON Utilities](#path-and-json-utilities)
  - [Introspection](#introspection)
  - [Testing and REPL Support](#testing-and-repl-support)
  - [Exceptions](#exceptions)
- [Application Flags](#application-flags)
  - [`search_upwards_for_project_dir`](#search_upwards_for_project_dir)
  - [`allow_execroot_override`](#allow_execroot_override)
  - [`allow_projectdir_override`](#allow_projectdir_override)
  - [`uses_locking`](#uses_locking)
  - [`uses_tkinter`](#uses_tkinter)

---

## Introduction

**lionscliapp** is a framework for building **small command-line tools that remember things**.

It is a humane CLI application framework for Python designed to make it easy to build **stateful developer tools** quickly.

Many useful command-line tools need memory — configuration, stored data, and project awareness. `lionscliapp` provides this infrastructure automatically so that developers can focus on writing command behavior instead of repeatedly implementing boilerplate.


### What It Provides

**Persistence.** When the tool runs from a directory, it creates a hidden project folder there (e.g. `.mytool/`) and keeps a `config.json` inside it. Users can set values once with `mytool set key value`; those values survive across invocations. The project folder can also hold other files your tool needs.

**Automatic CLI parsing.** You do not write an argument parser. You declare keys, and the framework handles parsing, persisting, and merging values. Options appear in `app.ctx` — a plain global dictionary — ready to use. You do not pass configuration around through function arguments.

**Multiple commands.** You can bind as many sub-commands as you like with `declare_cmd`. You can also declare a default (no-command) handler so the tool does something sensible when invoked without a sub-command.

**Paths are native.** CLI tools work with files constantly. Any key prefixed with `path.` is automatically converted to a `pathlib.Path` — expanded, resolved, ready to use. You also get `read_json()` and `write_json()` that take path names directly, so reading or writing a JSON file is a one-liner.

**JSON is native.** The framework is built on the idea that JSON files are a good communication format between programs — readable, diffable, inspectable. Reading a named JSON input and writing a named JSON output requires no `import json`, no open/close, no path construction. Just `app.read_json("input")` and `app.write_json("output", data)`.

**Built-in commands.** `set`, `get`, `keys`, `help`, and `help-basics` are always available without any work on your part. If the application enables locking with `app.set_flag("uses_locking", True)`, the built-in `unlock` command is also available.

**Optional Tkinter runtime support.** If the application enables Tk support with `app.set_flag("uses_tkinter", True)`, selected commands can behave as single-instance GUI commands. A later invocation writes a generic JSON message into the app's `inbox/` directory and summons the existing window instead of launching another GUI against the same data.

### What It Doesn't Do

`lionscliapp` is deliberately simple. With the exception of `path.*` keys, and a couple special purpose keys, **all configuration values are treated as strings**. There is no built-in system for declaring integer options, boolean flags, enums, or validated choices. If you need those, you coerce from `app.ctx` yourself:

```python
def my_cmd():
    count = int(app.ctx["retry.count"])
    verbose = app.ctx["verbose"].lower() == "true"
```

This is a deliberate trade-off: a simpler mental model in exchange for less automatic type handling.

### Design Ethos

**Globals are good here.** CLI tools run once, in a single process, with a single context. Threading global state through every function is noise without benefit. `app.ctx` is global and honest about it.

**JSON is the universal substrate.** All declared data must be JSON-serializable. Configuration is JSON.

**No classes.** The core architecture uses plain dictionaries and named functions. Data and behavior are kept separate. This is intentional, not an oversight.

**Flags as semantic splitters.** Functions that do one thing in multiple ways take a short flag character rather than proliferating narrow variants. `mode="c"` means *configured*; `mode="p"` means *project-relative*.

---

## Getting Started

### Installation

```bash
pip install -e .
```

Requires Python 3.10+.

### A Complete Example

Here is a small but complete tool called `filetool` that demonstrates the framework.

```python
# filetool.py
import lionscliapp as app

# --- Declarations ---

app.declare_app("filetool", "1.0")
app.describe_app("A tool for file operations")

app.declare_projectdir(".filetool")

app.declare_key("path.inbox",  "~/inbox")
app.declare_key("path.output", "~/output")
app.declare_key("json.indent.results", "2")

app.describe_key("path.inbox",         "Where incoming files are read from")
app.describe_key("path.output",        "Where output files are written")
app.describe_key("json.indent.results","Indent level for results JSON")

def cmd_process():
    inbox  = app.ctx["path.inbox"]   # pathlib.Path
    output = app.ctx["path.output"]  # pathlib.Path

    print(f"Reading from: {inbox}")
    print(f"Writing to:   {output}")
    # ... do actual work ...

def cmd_status():
    print("All good.")

app.declare_cmd("process", cmd_process)
app.describe_cmd("process", "Process inbox files into output")

app.declare_cmd("status", cmd_status)
app.describe_cmd("status", "Check system status")

# --- Entry point ---

app.main()
```

**Running the tool:**

```bash
# Show help
python filetool.py help

# List all keys and their descriptions
python filetool.py keys

# Persist a config value
python filetool.py set path.output ~/my-output

# Inspect a key (shows default, stored value, and current value)
python filetool.py get path.output

# Run a command (uses persisted config)
python filetool.py process

# Override a value for this invocation only (not persisted)
python filetool.py --path.inbox /tmp/test process

# Load a batch of overrides from a file
python filetool.py --options-file dev-overrides.json process
```

After `python filetool.py set path.output ~/my-output`, a file called `.filetool/config.json` is created in the current directory:

```json
{
  "options": {
    "path.output": "~/my-output"
  }
}
```

The next time the tool runs from that directory, it reads this file and `app.ctx["path.output"]` is already set to `Path("~/my-output").expanduser()`.

---

## Keys and Namespaces

### What a Key Is

Keys are dot-namespaced strings declared with `app.declare_key(key, default)`. They form the configuration vocabulary of your tool. When the framework starts, all key values — merged from their various sources — are placed in `app.ctx`, the global configuration dictionary.

```python
app.declare_key("path.output", "~/output")
app.declare_key("path.input",  "~/input")
app.declare_key("log.prefix",  "INFO")
```

### Values Are Strings

When a user sets a value from the command line (`--key value` or `mytool set key value`), it arrives as a plain string. The framework does not try to infer types. This means that if you declare:

```python
app.declare_key("retry.count", "3")
```

and the user runs `mytool set retry.count 5`, `app.ctx["retry.count"]` will be the string `"5"`. If you need an integer, coerce it yourself:

```python
def my_cmd():
    count = int(app.ctx["retry.count"])
```

Use string defaults for keys that users will configure. This keeps the contract clear.

### `path.*` — The Special Case

Any key prefixed with `path.` is treated differently: its value is converted to a `pathlib.Path` before it reaches `app.ctx`.

- `~` is expanded via `Path.expanduser()`.
- Relative paths are resolved against the execution root (the directory the tool was run from).
- Absolute paths are left as-is.

```python
app.declare_key("path.output", "~/output")
app.declare_key("path.input",  "~/input")

# In your command:
p = app.ctx["path.output"]  # pathlib.Path, fully resolved
p.mkdir(parents=True, exist_ok=True)
```

This is the main reason to use the `path.` prefix. It also makes `path.*` keys work directly with `get_path()`, `read_json()`, and `write_json()` (see below).

### `json.indent.*` — JSON Output Configuration

This namespace exists specifically to configure the behaviour of `write_json()`. It is not general-purpose coercion; it is wired into the JSON I/O system.

- `json.indent.<id>` — the indentation level (coerced to int) to use when writing the JSON file identified by `<id>`. A value of `0` means compact output with no whitespace.

```python
app.declare_key("json.indent.results", 2)
```

When `write_json("results", data)` is called in configured mode, it checks this key and formats the output accordingly. This lets users control formatting with `mytool set json.indent.results 4` or `mytool set json.indent.results 0` (compact) without any extra code in your commands.

See the [JSON I/O](#json-io) section for full details.

### The ctx Dictionary

`app.ctx` is a plain Python dictionary populated by `app.main()` just before dispatching to your command.

```python
def my_command():
    print(app.ctx["path.output"])  # pathlib.Path
    print(app.ctx["log.prefix"])   # "INFO" (string)
```

Do not read `app.ctx` during the declaration phase (before `app.main()`). It is empty at that point.

---

## Configuration Layering

Values in `app.ctx` are assembled from four layers. Later layers override earlier ones.

| Layer | Source | Persists? |
|-------|--------|-----------|
| 1. Defaults | `declare_key(key, default)` | — |
| 2. Config file | `.filetool/config.json` (written by `set`) | Yes |
| 3. Options file | `--options-file path.json` | No |
| 4. CLI overrides | `--key value` on command line | No |

This means:
- A value set with `mytool set path.output ~/out` survives across invocations.
- A value passed as `mytool --path.output /tmp run` is used only for that run.
- An options file is useful for scripted environments or per-environment config.

### Config File Format

The config file is written and read automatically. You can inspect it directly:

```json
{
  "options": {
    "path.output": "~/my-output",
    "log.prefix": "DEBUG"
  }
}
```

### Options File Format

An options file has the same structure as the config file:

```json
{
  "options": {
    "path.output": "/ci/build/output",
    "json.indent.results": 0
  }
}
```

Load it with:

```bash
mytool --options-file ci-config.json process
```

Relative paths in `--options-file` are resolved against the execution root.

---

## Built-in Commands

These built-in commands are available without declaration and cannot be overridden. `unlock` appears only when locking is enabled for the application.

### `set <key> <value>`

Persist a configuration value to `config.json`. The value is stored as a string.

```bash
mytool set path.output ~/my-output
mytool set json.indent.results 4
```

After `set`, the value is immediately reflected in `app.ctx` for the current invocation (though there is rarely a reason to run another command in the same invocation).

### `get <key>`

Show the current state of a key, broken down by layer.

```bash
mytool get path.output
```

Output shows the declared default, the stored config file value (if any), and the current resolved value.

### `keys`

List all declared configuration keys with their short descriptions.

```bash
mytool keys
```

### `help [command]`

Show application help. Without an argument, lists all commands and options. With a command name, shows detailed help for that command.

```bash
mytool help
mytool help process
```

### `help-basics`

Show framework-oriented help for `lionscliapp` itself rather than the hosted application's specific commands.

This includes things like:

- what `--execroot` changes
- what `--project-dir` changes
- how configuration layering works
- what the built-in commands are
- what special key namespaces such as `execpath.*`, `projpath.*`, and `json.indent.*` mean

```bash
mytool help-basics
```

### `unlock`

Remove a stale `lock.json` file from the project directory.

This command is available only when the application enables locking with `app.set_flag("uses_locking", True)`.

Use it when a previous lock-requiring command crashed or the machine lost power and left the project locked.

```bash
mytool unlock
```

---

## CLI Global Options

These options are parsed before the command and apply to any invocation.

### `--<key> <value>`

Override a configuration value for this invocation only (not persisted).

```bash
mytool --path.output /tmp/test process
mytool --retry.count 1 process
```

Multiple overrides can be combined:

```bash
mytool --path.inbox /tmp/in --path.output /tmp/out process
```

### `--options-file <path>`

Load a batch of configuration overrides from a JSON file. The file must contain an `"options"` object.

```bash
mytool --options-file dev.json process
```

### `--execroot <path>`

Override the execution root directory. By default the execution root is the current working directory. This option is only accepted if the application set `allow_execroot_override` to `True`.

```bash
mytool --execroot /other/project process
```

### `--project-dir <name>`

Override the project directory name for this invocation. This is a directory **name** only (no slashes), not a full path. The overridden name is used when searching upward for the project directory, and the project directory is still located under the execution root.

This option is only accepted if the application set `allow_projectdir_override` to `True`.

```bash
mytool --project-dir .mytool-staging process
```

---

## Path Resolution

### `app.get_path(id, mode="c")`

Resolve a path using one of four modes.

| Mode | Meaning |
|------|---------|
| `"c"` | Configured: looks up `app.ctx["path.<id>"]` |
| `"p"` | Project: resolves `<id>` relative to the project directory |
| `"e"` | Execroot: resolves `<id>` relative to the execution root |
| `"f"` | Filesystem: treats `<id>` as a literal path (absolute, or relative to cwd) |

```python
def my_cmd():
    # Configured mode (default): reads ctx["path.output"]
    p = app.get_path("output")

    # Project mode: project_dir/results.json
    p = app.get_path("results.json", "p")

    # Execroot mode: execroot/data/input.json
    p = app.get_path("data/input.json", "e")

    # Filesystem mode: literal path
    p = app.get_path("/absolute/path/to/file.json", "f")
```

All modes return an absolute `pathlib.Path`.

---

## JSON I/O

These utilities integrate path resolution and format configuration so you do not have to manage them manually.

### `app.read_json(id, mode="c")`

Read and parse a JSON file. The `mode` is a path mode character (`c`, `p`, `e`, `f`).

```python
def my_cmd():
    data = app.read_json("input")          # reads ctx["path.input"]
    data = app.read_json("data.json", "p") # reads <project_dir>/data.json
    data = app.read_json("results.json", "e") # reads <execroot>/results.json
```

Raises `FileNotFoundError` if the file does not exist. Raises `json.JSONDecodeError` if the file is not valid JSON.

### `app.write_json(id, data, mode="c")`

Write data to a JSON file. The `mode` string can contain a path flag and an optional format flag.

**Path flags:** `c`, `p`, `e`, `f` (same as `get_path`).

**Format flags:**

| Flag | Meaning |
|------|---------|
| `"2"` | Pretty: indent with 2 spaces (default) |
| `"0"` | Compact: no whitespace |

```python
def my_cmd():
    results = {"count": 42, "items": [...]}

    # Configured path, formatting read from ctx if declared
    app.write_json("output", results)

    # Configured path, force pretty format
    app.write_json("output", results, "c2")

    # Configured path, force compact (minified) format
    app.write_json("output", results, "c0")

    # Project-relative path, pretty format
    app.write_json("cache.json", results, "p2")

    # Literal path
    app.write_json("/tmp/debug.json", results, "f")
```

**Format from ctx (configured mode only):** When using mode `"c"` without an explicit format flag, `write_json` checks `app.ctx` for `json.indent.<id>`. If declared, that integer is used as the indent level; `0` means compact (no whitespace). If not declared, the default is indent=2.

---

## Tkinter Runtime

The Tkinter runtime subsystem is optional. It is for GUI commands that should behave as single-instance applications while still using normal `lionscliapp` argument parsing, project-dir handling, and command dispatch.

When enabled:

- the live GUI owner is tracked in `<project_dir>/instance.json`
- a generic FileTalk-style mailbox lives in `<project_dir>/inbox/`
- later invocations of a `single_instance` Tk command write a JSON message into `inbox/` and return successfully instead of launching another GUI
- the live GUI process polls `inbox/` on the Tk event loop and can react to any message type, not just `summon`

Recommended declaration pattern:

```python
app.set_flag("uses_tkinter", True)
app.declare_cmd("", cmd_ui)
app.set_cmd_flag("", "tkinter", True)
app.set_cmd_flag("", "single_instance", True)

app.declare_key("runtime.gui.inbox.poll_ms", "1000")
app.declare_key("runtime.tests.enabled", "false")
app.declare_key("runtime.tests.isolated", "false")
```

### `app.attach_tk(root, message_handler=None)`

Attach the Tk runtime to a live Tk root-like object.

```python
def cmd_ui():
    root = tkinter.Tk()
    app.attach_tk(root, handle_runtime_message)
    root.mainloop()
```

This schedules recurring inbox polling via `root.after(...)`.

### `app.send_message(message)`

Write a generic JSON message into `<project_dir>/inbox/`.

```python
app.send_message({
    "type": "reload-data",
    "created": "2026-06-24T12:00:00Z"
})
```

The mailbox is generic. `summon` is only one message type among others.

### `app.consume_messages()` and `app.poll_inbox_once()`

`consume_messages()` reads and deletes complete JSON messages from `inbox/`.
`poll_inbox_once()` does one consume-and-dispatch pass using the currently attached Tk root and message handler.

Incomplete or invalid JSON files are left in place and retried on a later poll, in the FileTalk style.

### `app.publish_instance_metadata(updates)`

Merge additional metadata into the owned `instance.json` record.

This is useful for publishing app-specific state such as a current folder, document id, or selected record.

### `app.bring_window_to_front(root)`

Best-effort foregrounding helper for Tk windows using Tk behaviors such as `deiconify()`, `lift()`, and `focus_force()`.

### `app.build_tkintertester_flags()` and `app.tests_enabled()`

Translate standard runtime test keys into `tkintertester` harness flags.

```python
flags = app.build_tkintertester_flags()
if app.tests_enabled():
    register_tests()
    harness.run_host(app_entry, flags)
```

Recognized keys:

- `runtime.tests.enabled`
- `runtime.tests.show`
- `runtime.tests.exit`

### Tk test safety

For Tk commands, if `runtime.tests.enabled` is truthy, the framework refuses to run unless both of these are true:

- `runtime.tests.isolated` is truthy
- `--project-dir` override is supplied

This is an intentional safety barrier against accidentally running GUI tests against a live data environment.

### Poll interval

Mailbox polling defaults to `1000` milliseconds. You can override it with:

```python
app.declare_key("runtime.gui.inbox.poll_ms", "800")
```

---

## Lifecycle Phases

The framework moves through three phases in order. Understanding them helps make sense of error messages.

| Phase | When | What's allowed |
|-------|------|----------------|
| `"declaring"` | Before `app.main()` | All `declare_*`, `describe_*`, `set_flag()` calls |
| `"running"` | Inside `app.main()`, command executing | Reading `app.ctx`; calling commands |
| `"shutdown"` | After command finishes | Nothing |

All declaration functions enforce the declaring phase. Calling `app.declare_key()` after `app.main()` raises a `RuntimeError`.

```python
phase = app.get_phase()  # "declaring", "running", or "shutdown"
```

---

## Complete Function Reference

### Declaration Functions

All declaration functions must be called before `app.main()`.

---

#### `app.declare_app(name, version)`

Set the application name and version string.

```python
app.declare_app("mytool", "1.0")
```

**Parameters:**
- `name` — Application name (string)
- `version` — Version string (string)

---

#### `app.describe_app(description, flags="")`

Set a description for the application.

```python
app.describe_app("A tool that does useful things")
app.describe_app("Extended details about what this tool does...", "l")
```

**Parameters:**
- `description` — Description text (string)
- `flags` — `""` or `"s"` sets the short description (default); `"l"` sets the long description

---

#### `app.declare_projectdir(name)`

Set the name of the project directory where `config.json` is stored. This directory is created under the execution root when the tool first runs.

```python
app.declare_projectdir(".mytool")
```

**Parameters:**
- `name` — Directory name (string, e.g. `".mytool"`)

---

#### `app.declare_cmd(name, fn)`

Bind a command name to a Python callable.

```python
def do_work():
    ...

app.declare_cmd("work", do_work)
```

**Parameters:**
- `name` — Command name (string)
- `fn` — Callable with no arguments

Built-in command names (`set`, `get`, `help`, `help-basics`, `keys`, and `unlock` when locking is enabled) cannot be used as user command names.

---

#### `app.describe_cmd(name, description, flags="")`

Set a description for a command.

```python
app.describe_cmd("work", "Run the main work process")
app.describe_cmd("work", "Full description of what work does...", "l")
```

**Parameters:**
- `name` — Command name (string)
- `description` — Description text (string)
- `flags` — `""` or `"s"` for short (default); `"l"` for long

---

#### `app.set_cmd_flag(name, flag_name, value)`

Set a boolean flag on a specific command.

```python
app.set_cmd_flag("sync", "locking", True)
```

**Parameters:**
- `name` — Command name (string)
- `flag_name` — Command flag name (string, e.g. `"locking"`)
- `value` — Boolean value to assign

Known command flags:

- `locking` — default `False`. If `True`, the command acquires `lock.json` just before execution and releases it afterward.
- `tkinter` — default `False`. Marks the command as a Tkinter runtime command.
- `single_instance` — default `False`. For Tkinter commands, later invocations summon the existing instance instead of launching another one.

Raises `ValueError` if `value` is not a `bool`.

---

#### `app.declare_key(key, default)`

Declare a configuration key with its default value.

```python
app.declare_key("path.output", "~/output")
app.declare_key("path.input",  "~/input")
app.declare_key("log.prefix",  "INFO")
```

**Parameters:**
- `key` — Key name (dot-namespaced string)
- `default` — Default value; must be JSON-serializable

The default is what `app.ctx[key]` returns if no other layer provides a value. For keys that users will set from the CLI or via the `set` command, use string defaults — values from those sources always arrive as strings. See [Keys and Namespaces](#keys-and-namespaces) for details.

---

#### `app.describe_key(key, description, flags="")`

Set a description for a configuration key.

```python
app.describe_key("path.output", "Where output files are written")
app.describe_key("path.output", "Full details about the output path...", "l")
```

**Parameters:**
- `key` — Key name (string)
- `description` — Description text (string)
- `flags` — `""` or `"s"` for short (default); `"l"` for long

---

#### `app.set_flag(flag_name, value)`

Set an application flag. Flags control framework behaviour such as whether certain CLI overrides are accepted.

```python
app.set_flag("allow_projectdir_override", True)
app.set_flag("search_upwards_for_project_dir", True)
app.set_flag("uses_locking", True)
app.set_flag("uses_tkinter", True)
```

**Parameters:**
- `flag_name` — Flag name string (e.g. `"allow_projectdir_override"`)
- `value` — Boolean value to assign

Raises `ValueError` if `value` is not a `bool`. See [Application Flags](#application-flags) for the available flags and their meanings.

---

#### `app.declare(spec)`

Mass-declare by deep-merging a specification dictionary into the application model. Useful for loading declarations from an external JSON file or for grouping related declarations.

```python
app.declare({
    "id": {
        "name": "mytool",
        "version": "1.0",
        "short_desc": "A useful tool"
    },
    "names": {
        "project_dir": ".mytool"
    },
    "options": {
        "path.output": {"default": "~/output", "short": "Output path"},
        "retry.count": {"default": 3}
    },
    "commands": {
        "work": {"short": "Do the work", "flags": {"locking": True}},
        "ui": {"short": "Open the interface", "flags": {"tkinter": True, "single_instance": True}}
    }
})
```

**Parameters:**
- `spec` — Dictionary following the application model structure

**Merge semantics:** Dictionaries are merged recursively. Scalar values use last-value-wins. `declare()` does not bind command functions — use `declare_cmd()` for that.

---

### Entry Point

#### `app.main()`

Start the application. This is always the last call in your script.

```python
app.main()
```

The framework:
1. Validates the application model
2. Parses CLI arguments
3. Resolves the execution root
4. Creates the project directory if needed
5. Loads `config.json`
6. Loads the options file (if `--options-file` was given)
7. Builds `app.ctx` by merging all layers (coercing `path.*` keys to `pathlib.Path`)
8. If needed, resolves Tkinter single-instance behavior for a Tk command
9. If needed, acquires `lock.json` for a lock-requiring command
10. Dispatches to the appropriate command

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Command executed successfully |
| `1` | Validation, configuration, or CLI parsing error |
| `2` | Unknown command or unbound function |
| `3` | Uncaught exception from the command |

---

### Runtime Context

#### `app.ctx`

A plain dictionary containing the merged, coerced configuration for the current invocation. Available during command execution.

```python
def my_cmd():
    out    = app.ctx["path.output"]          # pathlib.Path
    prefix = app.ctx["log.prefix"]           # "INFO" (string)
```

`app.ctx` is empty before `app.main()` runs. Do not read it at module level or during declarations.

---

### Path and JSON Utilities

#### `app.get_path(id, mode="c")`

Resolve a path. Returns an absolute `pathlib.Path`.

```python
p = app.get_path("output")              # ctx["path.output"] as Path
p = app.get_path("cache.json", "p")    # <project_dir>/cache.json
p = app.get_path("data/in.json", "e")  # <execroot>/data/in.json
p = app.get_path("/abs/path.json", "f")# literal path
```

**Parameters:**
- `id` — Key name (for `"c"`), filename or subpath (for `"p"`, `"e"`), or literal path (for `"f"`)
- `mode` — One of `"c"` (configured), `"p"` (project), `"e"` (execroot), `"f"` (filesystem)

---

#### `app.read_json(id, mode="c")`

Read and parse a JSON file. Returns the parsed Python value.

```python
data = app.read_json("input")           # reads ctx["path.input"] file
data = app.read_json("state.json", "p") # reads <project_dir>/state.json
```

**Parameters:**
- `id` — Path identifier (interpretation depends on mode)
- `mode` — Path mode: `"c"`, `"p"`, `"e"`, or `"f"`

Raises `FileNotFoundError` if the file does not exist.
Raises `json.JSONDecodeError` if the file contains invalid JSON.

---

#### `app.write_json(id, data, mode="c")`

Write Python data as JSON to a file. Creates parent directories if needed. Adds a trailing newline.

```python
app.write_json("output", results)          # configured path, ctx formatting
app.write_json("output", results, "c2")   # configured path, pretty
app.write_json("output", results, "c0")   # configured path, compact
app.write_json("log.json", log, "p")      # <project_dir>/log.json
app.write_json("/tmp/dbg.json", d, "f")   # literal path
```

**Parameters:**
- `id` — Path identifier
- `data` — JSON-serializable value to write
- `mode` — Mode string: a path flag (`c`, `p`, `e`, `f`) optionally followed by a format flag (`2` for pretty, `0` for compact)

In `"c"` mode without an explicit format flag, formatting is read from `app.ctx`:
- `json.indent.<id>` — indent level (integer); `0` means compact (no whitespace)

If that key is not declared, the default is 2-space indent.

---

### Introspection

#### `app.get_phase()`

Return the current execution phase as a string.

```python
phase = app.get_phase()  # "declaring", "running", or "shutdown"
```

Useful in tests or for conditional logic that needs to know whether declarations are still possible.

---

### Testing and REPL Support

#### `app.reset()`

Reset all global framework state to the initial declaring-ready state. Intended for tests and interactive use.

```python
app.reset()
```

After `reset()`, all declarations are cleared and the phase returns to `"declaring"`. This allows multiple tests to run against fresh framework state in the same process.

Example test pattern:

```python
import lionscliapp as app

def setup_function():
    app.reset()

def test_my_command():
    app.declare_app("test", "1.0")
    app.declare_projectdir(".test")
    app.declare_key("path.output", "/tmp/out")
    app.declare_cmd("run", lambda: None)
    # ... invoke and assert ...
```

---

### Exceptions

#### `app.StartupError`

Raised by `app.main()` for errors that occur before dispatch: validation failures, missing declarations, bad CLI syntax, or config file problems.

```python
from lionscliapp import StartupError
```

Exit code: `1`.

#### `app.DispatchError`

Raised by `app.main()` when the command name is not recognized or a command function is not bound.

```python
from lionscliapp import DispatchError
```

Exit code: `2`.

---

## Application Flags

Flags control optional framework behaviours. Set them with `app.set_flag()` during the declaring phase.

### `search_upwards_for_project_dir`

When `True`, the framework walks up the directory tree from the current working directory looking for a parent that contains the project directory. This makes the tool usable from subdirectories of a project, similar to how `git` finds `.git`.

```python
app.set_flag("search_upwards_for_project_dir", True)
```

Default: `False`.

### `allow_execroot_override`

When `True`, the `--execroot` CLI option is accepted. When `False`, passing `--execroot` causes a startup error.

```python
app.set_flag("allow_execroot_override", False)
```

Default: `True`.

### `allow_projectdir_override`

When `True`, the `--project-dir` CLI option is accepted, allowing callers to override the project directory name for a single invocation. The value must be a plain directory name with no path separators. When `False`, passing `--project-dir` causes a startup error.

```python
app.set_flag("allow_projectdir_override", False)
```

### `uses_locking`

Enable framework-managed command locking.

```python
app.set_flag("uses_locking", True)
app.set_cmd_flag("sync", "locking", True)
```

When enabled:

- commands marked with `locking=True` create `lock.json` in the resolved project directory just before execution
- the lock file records `lock_id`, `command`, `pid`, and `created_at`
- the file is removed after successful completion or after an uncaught command exception
- a stale lock can be cleared with the built-in `unlock` command

Default: `False`.

### `uses_tkinter`

Enable the optional Tkinter single-instance runtime subsystem.

```python
app.set_flag("uses_tkinter", True)
app.set_cmd_flag("ui", "tkinter", True)
app.set_cmd_flag("ui", "single_instance", True)
```

When enabled:

- commands marked with `tkinter=True` are treated as Tk runtime commands
- commands also marked with `single_instance=True` use `instance.json` ownership and `inbox/` messaging
- later invocations summon the existing instance instead of launching another GUI
- the live instance can receive any JSON messages through the generic FileTalk-style mailbox

Default: `False`.
