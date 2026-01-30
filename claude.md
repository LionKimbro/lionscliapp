
# claude.md

### Notes on Design Philosophy for `lionscliapp` (and Related Projects)

This document explains several **deliberate design choices** used throughout `lionscliapp` and related Lion Kimbro projects. These choices may differ from common Python or enterprise frameworks. They are intentional, tested in practice, and optimized for clarity, inspectability, and humane tooling.

This is not a list of rules to follow blindly — it is an explanation of *why the system looks the way it does*.

---

## 1. Globals Are Good (When Used Correctly)

This framework **intentionally uses global state** (e.g. `app.ctx`).

This is not accidental and not a shortcut.

### Why globals are used here

* The execution model is:

  * single-process
  * single application instance
  * single execution lifecycle
* CLI tools are **not concurrent systems**
* There is exactly one meaningful runtime context at a time

In this environment, a global:

* **improves inspectability**
* **reduces plumbing**
* **matches the mental model of the user**
* avoids passing the same object through every function “just because”

### What globals are *not* used for

* Hidden mutation across threads
* Long-lived background state
* Implicit side effects outside the execution lifecycle

Globals are paired with:

* explicit lifecycle phases
* mutation guards
* deterministic construction

> A global that is *honestly global* is clearer than a pseudo-global threaded through arguments.

---

## 2. JSON Is the Universal Substrate

This framework treats **JSON as the lingua franca** between:

* humans
* programs
* tools
* future orchestration systems

### Why JSON everywhere

* JSON is:

  * readable
  * diffable
  * serializable
  * inspectable
  * language-agnostic
* JSON structures can be:

  * logged
  * cached
  * transmitted
  * replayed
  * transformed

Even when runtime types are richer (e.g. `pathlib.Path`), there must always exist a **lossless JSON representation**.

This is why:

* configuration is JSON
* ctx has a logical JSON form
* declarative specs are JSON-compatible

> If a value cannot survive JSON, it does not belong in the declarative surface.

---

## 3. No Classes (Yes, Really)

This project **deliberately avoids classes** in the core architecture.

This is not anti-OOP ideology — it is a *practical constraint*.

### Why classes are avoided

Classes tend to:

* hide state across methods
* encourage implicit coupling
* complicate serialization
* make inspection harder
* blur the line between data and behavior

In contrast, this framework prefers:

* explicit dictionaries
* named functions
* declarative schemas
* data-first models

### Where behavior belongs

* **Data** is declared declaratively
* **Behavior** is bound explicitly via functions
* The boundary between the two is sharp and intentional

Callable values are allowed *only* where explicitly specified (e.g. command functions).

> Classes are excellent for some domains.
> This is not one of them.

---

### 4. Flags Are Semantic Splitters, Not Arguments

In this codebase, **flags are not a workaround** and not a legacy artifact.
They are a **first-class design tool**.

Flags are used when:

* A function represents a **high-value action**
* That action has **multiple concrete realizations**
* The *verb itself should remain stable*

Instead of creating many narrowly-named functions, we prefer:

* **one stable verb**
* **a small flag vocabulary**
* **long, explicit internal helpers**

#### Why this works

Function calls are never read in isolation.

They are read inside a *story*.

```python
def handle_when_user_clicks_save_button():
    text = read_text("editor")
    save_text(text, "F")
```

The handler name, surrounding logic, and flow already constrain the meaning.
The flag does not introduce ambiguity — it **confirms intent**.

Inside the implementation, clarity is expanded, not compressed:

```python
def save_text(text, flags="F"):
    if flags == "F":
        _save_text_to_file(text)
    elif flags == "N":
        _save_text_to_network(text)
    elif flags == "D":
        _save_text_to_dictionary(text)
```

This creates a **dual-tier architecture**:

* **Simple at call sites**
* **Explicit inside**

Flags are only effective when:

* each flag has one stable meaning system-wide
* the surrounding context already carries most of the meaning

Used this way, flags:

* reduce namespace clutter
* preserve conceptual unity
* keep call sites readable
* allow internal structure to grow without API sprawl

---

### 5. Function Names Are a Map, Not Labels

Function naming in this project is **not about descriptiveness alone**.
It is about giving the codebase **shape, hierarchy, and terrain**.

Names encode:

* frequency
* scope
* reuse expectations
* narrative role
* boundary crossings

A reader should be able to *scan* a file and immediately see:

* where the main currents flow
* where a detour occurs
* where an external event enters

#### 5.1 Primitives — One Word

Functions called constantly form the **core vocabulary**.

Examples:

```python
send(msg)
recv()
push(obj)
pop()
flush()
```

Characteristics:

* extremely high frequency
* minimal conceptual weight
* meaning refined by context and flags
* never over-specified

These are the highways.

---

#### 5.2 General Functions — `verb_object`

Most reusable functionality lives here.

Examples:

```python
send_message(msg, flags="")
store_photo(data)
lookup_key(k)
process_event(evt)
```

These are the main roads:

* predictable
* steady
* broadly applicable
* context-aware

---

#### 5.3 One-Off Functional Units — Long, Prose-Like Names

If a function is only ever called from **one place**, it should **say exactly what it does**.

Examples:

```python
rebuild_everything_from_disk_now()
check_for_restart_request_and_handle()
update_filetree_cache_after_reload()
```

These functions are:

* labeled code blocks
* outline nodes
* narrative segments

They are not reusable tools — they are **named moments in the story**.

---

#### 5.4 Predicates — Questions, Not Computations

Predicates return booleans and must **read like questions**.

There are two kinds:

##### System-Wide Predicates (Short)

Reusable, high-frequency checks:

```python
is_system_ready()
has_pending_uploads()
should_retry_later()
may_attempt_reconnect()
```

These form the **decision vocabulary** of the system.

##### Single-Context Predicates (Long)

Used once, narrative, descriptive:

```python
should_we_reload_everything_from_disk_now()
has_user_already_selected_a_photo_this_session()
```

These exist to:

* segment logic
* name decisions
* improve scanability

---

#### 5.5 Callback Handlers — City Gates

Callback handlers are invoked by **external systems**.

They are:

* single-source
* event-specific
* boundary crossings

They must:

* begin with `handle_` or `on_`
* use long, narrative names

Examples:

```python
handle_when_user_clicks_save_button(event)
handle_after_receiving_mqtt_message_from_desktop(msg)
handle_when_socket_connection_fails(error)
```

These names turn stack traces into readable stories.

---

### Closing Principle

These conventions exist to make the codebase:

* readable as a map, not a maze
* easy to navigate without memorization
* expressive without clutter
* pleasant to live inside

Short names are *earned*.
Long names are *labels*.
Flags preserve unity.
Context carries meaning.

If this style feels unfamiliar, read the code as **terrain**, not syntax.


## 6. Constraints Are Features

Many “missing” features are **intentionally excluded** in v0:

* environment variable overrides
* logging frameworks
* positional arguments
* alternative config formats
* concurrency abstractions

These are not oversights.

They are excluded to:

* keep the mental model small
* preserve inspectability
* avoid premature generalization

They may appear in future versions — **but only when they earn their place**.

---

## Closing Note

This framework is designed to support:

* humane CLI tools
* inspectable execution
* long-lived tooling ecosystems
* future orchestration (FileTalk / Patchboard style)

If a design choice seems unusual, assume it is **constrained on purpose**, not forgotten.

Questions are welcome.
Unexamined “best practices” are not.

