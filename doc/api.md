# lionscliapp API Reference

This document describes the public API of `lionscliapp`.

```python
import lionscliapp as app
```

---

## Declaration Functions

These functions define your application's structure. They must be called **before** `app.main()`.

### `declare_app(name, version)`

Declare the application name and version.

```python
app.declare_app("mytool", "1.0")
```

**Parameters:**
- `name` — Application name (string)
- `version` — Application version (string)

---

### `describe_app(description, flags="")`

Set a short or long description for the application.

```python
app.describe_app("A tool that does useful things")
app.describe_app("Extended description with more details...", "l")
```

**Parameters:**
- `description` — Description text
- `flags` — `""` or `"s"` for short description (default), `"l"` for long description

---

### `declare_projectdir(name)`

Declare the project directory name for persistent configuration.

```python
app.declare_projectdir(".mytool")
```

**Parameters:**
- `name` — Directory name (e.g., `".mytool"`)

The project directory is created under the execution root and stores `config.json`.

---

### `declare_cmd(name, fn)`

Bind a command name to a callable function.

```python
def run_command():
    print("Running...")

app.declare_cmd("run", run_command)
```

**Parameters:**
- `name` — Command name (string), or `""` for no-command dispatch
- `fn` — Callable to execute when command is invoked

---

### `describe_cmd(name, description, flags="")`

Set a short or long description for a command.

```python
app.describe_cmd("run", "Run the main process")
app.describe_cmd("run", "Detailed explanation of what run does...", "l")
```

**Parameters:**
- `name` — Command name
- `description` — Description text
- `flags` — `""` or `"s"` for short (default), `"l"` for long

---

### `declare_key(key, default)`

Declare a configuration key with its default value.

```python
app.declare_key("path.output", "/tmp/output")
app.declare_key("json.indent.data", 2)
```

**Parameters:**
- `key` — Option key (dot-namespaced string, e.g., `"path.output"`)
- `default` — Default value (must be JSON-serializable)

---

### `describe_key(key, description, flags="")`

Set a short or long description for a configuration key.

```python
app.describe_key("path.output", "Output file path")
```

**Parameters:**
- `key` — Option key
- `description` — Description text
- `flags` — `""` or `"s"` for short (default), `"l"` for long

---

### `declare(spec)`

Mass declaration by deep-merging a specification dict into the application.

```python
app.declare({
    "id": {
        "name": "mytool",
        "version": "1.0",
        "short_desc": "A useful tool"
    },
    "options": {
        "path.output": {"default": "/tmp/out"}
    }
})
```

**Parameters:**
- `spec` — Dictionary to merge into the application model

**Merge semantics:**
- Dicts are merged recursively by key
- Scalars use last-value-wins

---

## Entry Point

### `main()`

Start the application lifecycle.

```python
app.main()
```

This function:
1. Validates the application model
2. Parses CLI arguments
3. Resolves execution root
4. Creates project directory if needed
5. Loads persistent configuration
6. Builds the runtime context (`ctx`)
7. Dispatches to the appropriate command

**Exit codes:**
- `0` — Command executed successfully
- `1` — Validation, configuration, or CLI parsing error
- `2` — Unknown command or unbound command function
- `3` — Uncaught exception during command execution

---

## Runtime Context

### `ctx`

A dictionary containing merged configuration values, accessible during command execution.

```python
def my_command():
    output_path = app.ctx["path.output"]  # Already a pathlib.Path
    indent = app.ctx["json.indent.data"]  # Already an int
```

Values in `ctx` are:
1. Merged from layers (defaults → config file → options file → CLI overrides)
2. Coerced by namespace prefix

**Namespace coercion rules:**

| Namespace | Coercion |
|-----------|----------|
| `path.*` | `pathlib.Path` (expanduser, relative paths resolved against execroot) |
| `json.rendering.*` | Validated enum: `"pretty"` or `"compact"` |
| `json.indent.*` | Integer ≥ 0 |
| (other) | No coercion (identity) |

---

## Introspection

### `get_phase()`

Return the current execution phase.

```python
phase = app.get_phase()  # "declaring", "running", or "shutdown"
```

**Phases:**
- `"declaring"` — Declarations are permitted (initial state)
- `"running"` — Application is executing; structural mutation forbidden
- `"shutdown"` — Program is terminating

---

## Testing & Reset

### `reset()`

Reset all global framework state to the initial declaring-ready state.

```python
app.reset()
```

Intended for tests, REPL use, and controlled development workflows. This forcefully resets state without lifecycle checks.

---

## Exceptions

### `StartupError`

Raised for validation, configuration, or CLI parsing errors during startup.

```python
from lionscliapp import StartupError
```

### `DispatchError`

Raised when command dispatch fails (unknown command, unbound function).

```python
from lionscliapp import DispatchError
```

---

## Built-in Commands

These commands are always available:

### `set <key> <value>`

Persist a configuration value to `config.json`.

```bash
mytool set path.output /new/path
```

### `get <key>`

Display the current value of a configuration key.

```bash
mytool get path.output
```

### `keys`

List all declared configuration keys with their short descriptions.

```bash
mytool keys
```

### `help`

Display application help (name, version, description, available commands).

```bash
mytool help
```

---

## CLI Options

### `--<key> <value>`

Override a configuration value for this invocation (not persisted).

```bash
mytool --path.output /tmp run
```

### `--options-file <path>`

Load configuration overrides from a JSON file.

```bash
mytool --options-file overrides.json run
```

### `--execroot <path>`

Override the execution root directory.

```bash
mytool --execroot /other/project run
```
