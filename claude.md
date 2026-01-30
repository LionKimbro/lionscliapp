
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

## 1.b. A note on globals use:

When there's a global dictionary, or a global list, in general, it should be manipulated IN-PLACE.

That is, if it contains a dictionary, it should be initialized with {}, and then cleared with D.clear().

If it is a list, it should be initialized with [], and then cleared with del L[:].


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

## 4. Flags Are Semantic Splitters, Not Arguments

In this codebase, **flags are a deliberate design mechanism**, not a workaround or legacy artifact.

Flags are used when:

* a function represents a high-value action
* that action has multiple concrete realizations
* the verb itself should remain stable

Instead of creating many narrowly named functions, the preferred structure is:

* one stable verb
* a small, system-wide flag vocabulary
* long, explicit internal helpers

### Design Rationale

Function calls are read **in context**, not in isolation.

```python
def handle_when_user_clicks_save_button():
    text = read_text("editor")
    save_text(text, "F")
```

The surrounding control flow already constrains meaning.
The flag disambiguates *how*, not *what*.

Internal clarity is expanded inside the function:

```python
def save_text(text, flags="F"):
    if flags == "F":
        _save_text_to_file(text)
    elif flags == "N":
        _save_text_to_network(text)
```

This produces a dual-tier structure:

* simple and readable at call sites
* explicit and extensible internally

Flags work when:

* each flag has one stable meaning everywhere in the system
* context already supplies most semantic weight

Used this way, flags reduce namespace clutter while preserving intent.

---

## 5. Function Names Encode Structure

Function naming in this project is used to make the **shape of the system visible**.

Name length and form signal:

* frequency of use
* scope of applicability
* reuse expectations
* narrative role
* boundary crossings

A reader should be able to scan a file and see:

* where the main flows are
* which functions are reusable
* which are single-use narrative segments
* where external events enter

---

#### 5.1 Primitives — One Word

Functions called extremely frequently form the core vocabulary.

Examples:

```python
send(msg)
recv()
push(obj)
pop()
flush()
```

Characteristics:

* very high frequency
* minimal conceptual weight
* meaning refined by context and flags
* never over-specified

---

#### 5.2 General Functions — `verb_object`

Most reusable functionality uses `verb_object` naming.

Examples:

```python
send_message(msg, flags="")
store_photo(data)
lookup_key(k)
process_event(evt)
```

These represent steady, predictable actions used across the system.

---

#### 5.3 One-Off Functional Units — Long Names

Functions called from exactly one location use long, descriptive names.

Examples:

```python
rebuild_everything_from_disk_now()
check_for_restart_request_and_handle()
update_filetree_cache_after_reload()
```

These functions act as labeled code blocks:

* not intended for reuse
* not part of the shared vocabulary
* used to segment and clarify flow

---

#### 5.4 Predicates — Questions

Predicates return booleans and must read like true/false questions.

##### System-Wide Predicates (Short)

Reusable checks used across the codebase:

```python
is_system_ready()
has_pending_uploads()
should_retry_later()
may_attempt_reconnect()
```

Allowed prefixes:

* `is_` — state
* `has_` — existence
* `should_` — policy or intent
* `may_` — permission or capability

##### Single-Context Predicates (Long)

Predicates used once, with narrative names:

```python
should_we_reload_everything_from_disk_now()
has_user_already_selected_a_photo_this_session()
```

These exist to segment logic without introducing new vocabulary.

---

#### 5.5 Callback Handlers — External Entry Points

Callback handlers mark boundaries where external systems invoke logic.

They must:

* begin with `handle_` or `on_`
* use long, descriptive names
* correspond to a specific event

Examples:

```python
handle_when_user_clicks_save_button(event)
handle_after_receiving_mqtt_message_from_desktop(msg)
handle_when_socket_connection_fails(error)
```

This makes event flow visible and stack traces readable.

---

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

