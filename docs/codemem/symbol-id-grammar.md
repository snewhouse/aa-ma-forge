# codemem SCIP-shaped Symbol ID Grammar (v1)

**Status:** pinned 2026-04-13, M1 Task 1.2b.
**Version:** schema v1 (M1).
**Source of truth:** `.claude/dev/active/codemem/codemem-reference.md` §Symbol IDs.

codemem symbol IDs are **SCIP-shaped** — they borrow Sourcegraph's SCIP moniker structure for interop with the Sourcegraph ecosystem, but we are not emitting Sourcegraph's protobuf wire format. The goal is a human-readable, grep-friendly, language-agnostic identifier that uniquely names any code symbol across an indexed repository.

---

## Grammar

```
SCIP-ID     := <scheme> ' ' <package> ' ' <descriptor>

scheme      := 'codemem'
package     := <repo-relative-directory-of-the-indexable>
               e.g. 'packages/codemem-mcp/src/codemem'
               e.g. '.'                    # if file is at repo root
               e.g. 'src'                  # multi-package repo root crate

descriptor  := <kind-marker> <file> '#' <symbol-path>

kind-marker := '/'  # term / def    (functions, variables, terms)
             | '#'  # type          (classes, interfaces, structs, enums)
             | '.'  # member        (methods, fields, enum variants, properties)

file        := <file-path-relative-to-package>
               # NOTE: file does NOT start with '/' — the leading '/' in a full
               # SCIP-ID is the kind-marker, not a path separator. Examples:
               e.g. 'storage/db.py'
               e.g. 'parser/ast_grep.py'

symbol-path := <name> ( ( '.' | '#' ) <name> )*
               # '.' for member-of  (class.method, enum.variant)
               # '#' for nested type (namespace#Inner)
```

### Three kind-markers only (v1)

| Marker | Meaning | Examples |
|---|---|---|
| `/` | Term / def | Standalone functions, top-level variables, Rust standalone fn |
| `#` | Type | Classes, interfaces, structs, traits, enums, type aliases |
| `.` | Member | Methods, fields, properties, enum variants, struct fields |

**Why only three:** v1 ships a minimal grammar. Future schema versions (v2+) may add markers for parameters, type params, macros, lifetimes — but v1 acceptance criteria only requires defs/calls/imports, so three markers suffice.

### Why the leading `/` before `<file>`

Separates `<package>` from `<file>` visually and makes the ID parseable via simple split on `/` and `#`:

```
codemem packages/codemem-mcp/src/codemem /storage/db.py#init_db
        └── package ──────────────────┘ └── file ────┘└── symbol-path
```

The space between `scheme` and `package` and between `package` and `descriptor` is the primary delimiter (also SCIP convention).

---

## Per-language examples

### Python

**Anatomy of a Python function ID:**

```
codemem packages/codemem-mcp/src/codemem /storage/db.py#init_db
└─┬──┘ └────────── package ──────────┘ │└── file ──┘│└ symbol ┘
  │                                    │            │
  scheme                               │            member separator
                                       │
                                       kind-marker '/' (term)
```

**Top-level function:**
```
codemem packages/codemem-mcp/src/codemem /storage/db.py#init_db
```
Kind: `/` (term)

**Class:**
```
codemem packages/codemem-mcp/src/codemem #storage/db.py#DBHelper
```
Kind: `#` (type)

**Method on a class:**
```
codemem packages/codemem-mcp/src/codemem .storage/db.py#DBHelper.connect
```
Kind: `.` (member); `symbol-path` = `DBHelper.connect`

**Decorated method (same encoding — decorators don't affect ID):**
```
codemem packages/codemem-mcp/src/codemem .storage/db.py#DBHelper.close
```
Decorator info is stored in `symbols.signature` column, NOT in the ID.

**Class with a metaclass (metaclass doesn't affect ID; stored in signature):**
```
codemem packages/codemem-mcp/src/codemem #storage/models.py#Registry
```

**Nested class:**
```
codemem packages/codemem-mcp/src/codemem #storage/models.py#Outer#Inner
```
Note `Outer#Inner` — the inner `#` separates nested types.

**Module-level variable / constant:**
```
codemem packages/codemem-mcp/src/codemem /storage/db.py#APPLICATION_ID
```
Kind: `/` (term).

**`__init__.py` file:**
```
codemem packages/codemem-mcp/src/codemem /storage/__init__.py#transaction
```
Package path stays at parent; `__init__.py` is just another file.

---

### TypeScript / JavaScript

**Standalone function:**
```
codemem src/web /utils/format.ts#formatDate
```

**Class:**
```
codemem src/web #components/UserCard.tsx#UserCard
```

**Method:**
```
codemem src/web .components/UserCard.tsx#UserCard.render
```

**Interface:**
```
codemem src/web #types/api.ts#UserResponse
```

**Type alias:**
```
codemem src/web #types/api.ts#UserID
```

**Namespace member (member of namespace-type):**
```
codemem src/web .utils/geometry.ts#Shape.area
```
(Inside `namespace Shape { export function area(...) }`)

**Nested TS namespace:**
```
codemem src/web #utils/geometry.ts#Shape#Circle
```

**Arrow function assigned to const at top level:**
```
codemem src/web /utils/handlers.ts#handleClick
```
Treated as term `/`.

---

### Java

**Class:**
```
codemem src/main/java #com/example/User.java#User
```

**Method:**
```
codemem src/main/java .com/example/User.java#User.getName
```

**Inner class (static or non-static):**
```
codemem src/main/java #com/example/User.java#User#Role
```
Outer `User`, inner `Role` separated by `#`.

**Anonymous class — identified by synthetic name `$N` where N is nth anonymous in the file:**
```
codemem src/main/java #com/example/Callbacks.java#Callbacks$1
codemem src/main/java .com/example/Callbacks.java#Callbacks$1.onSuccess
```
`$1` = first anonymous class in `Callbacks.java`. This is a **parser convention**, not Java language semantics; codemem's parser assigns `$1`, `$2`, ... in file-declaration order.

**Enum:**
```
codemem src/main/java #com/example/Status.java#Status
codemem src/main/java .com/example/Status.java#Status.ACTIVE
```

---

### Go

**Standalone function:**
```
codemem cmd/server /main.go#main
codemem internal/user /repo.go#FindByID
```

**Type (struct):**
```
codemem internal/user #repo.go#Repository
```

**Method on receiver — receiver name is part of symbol-path:**
```
codemem internal/user .repo.go#Repository.FindByID
codemem internal/user .repo.go#(*Repository).Save
```
Pointer receivers: encode receiver as `(*Type)` to disambiguate from value receivers. Parser emits this form exactly as it appears in source.

**Interface:**
```
codemem internal/user #repo.go#Storage
```

---

### Rust

**Standalone function:**
```
codemem src /lib.rs#init
```

**Struct:**
```
codemem src #models.rs#User
```

**Impl block method — receiver is the type:**
```
codemem src .models.rs#User.new
codemem src .models.rs#User.find_by_id
```
Both `impl User { fn new() {} }` and `impl User { fn find_by_id(&self) {} }` map to `#User.XXX`.

**Trait:**
```
codemem src #traits.rs#Storage
```

**Trait method (default impl or trait signature):**
```
codemem src .traits.rs#Storage.get
```

**Impl Trait for Type — method is scoped to the type, not the trait (v1 convention):**
```
codemem src .models.rs#User.get
```
(from `impl Storage for User { fn get(&self) -> ... }`)

Rationale: the symbol's callable location is on `User`, not on `Storage` itself. Trait-scoped queries can intersect `User.get` with `Storage.get` via the edges table (both emit rows).

**Macro definition:**
Not supported in v1 (ast-grep's Rust grammar does not resolve macro bodies deterministically). Macros are stored as `term /` but their bodies aren't parsed — may be revisited in v2.

---

### Ruby

**Class:**
```
codemem lib #models/user.rb#User
```

**Method:**
```
codemem lib .models/user.rb#User.find_by_id
```

**Module:**
```
codemem lib #util/strings.rb#Strings
```

**Module method:**
```
codemem lib .util/strings.rb#Strings.titleize
```

---

### Bash

Limited: only function defs are extracted.

```
codemem scripts /install.sh#check_prereqs
```
All bash symbols use `/` kind.

---

## Uniqueness & conflicts

**Within a file, `(file_id, scip_id)` is UNIQUE** (enforced at schema level, see `schema.sql` `symbols` table).

**Across files, same-named symbols are distinct**: `codemem src /a.py#foo` and `codemem src /b.py#foo` are different rows.

**Overloaded functions (Java, TypeScript overloads, Rust trait default impls):** v1 emits ONE row per overload, differentiated by `signature_hash` in the `symbols` column — IDs collide, hash disambiguates. Post-M1 may revisit if collision rate is high (add `#N` suffix for Nth overload).

**Generic / parameterized types:** v1 encodes the base type name only. `Foo<T>` and `Foo<U>` both map to `#models.rs#Foo`. Type parameters live in `signature`, not the ID.

---

## Why this shape, not vanilla SCIP

Sourcegraph's SCIP moniker format supports many more descriptor kinds (`(`, `)`, `[`, `]`, `+`, `-`, etc. for parameters, type params, signatures). codemem v1 does not need them — our query layer is symbol-level, not signature-level, and packing that extra info into IDs would:

1. Bloat the `symbols.scip_id` TEXT column (disk + index cost)
2. Complicate grep-friendliness of the ID (core KISS goal)
3. Slow rename detection (M2 — more ID noise = more SequenceMatcher work)

If cross-ecosystem interop with Sourcegraph's SCIP consumers becomes a hard requirement, we emit SCIP-proper via a separate `codemem export-scip` command; internally we keep the leaner shape.

---

## Parser contract (M1 Steps 1.3 + 1.4)

Parsers MUST produce SCIP IDs matching this grammar. Each parser implementation (`codemem.parser.python_ast`, `codemem.parser.ast_grep`) has a golden fixture test in `tests/codemem/test_symbol_ids_<lang>.py`:

**Fixture shape:**
```python
# tests/fixtures/codemem/symbol_ids/python_sample.py
def foo(): ...
class Bar:
    def baz(self): ...
    @staticmethod
    def qux(): ...
class Outer:
    class Inner: ...
```

**Expected emit set:**
```python
[
    "codemem tests/fixtures/codemem/symbol_ids /python_sample.py#foo",
    "codemem tests/fixtures/codemem/symbol_ids #python_sample.py#Bar",
    "codemem tests/fixtures/codemem/symbol_ids .python_sample.py#Bar.baz",
    "codemem tests/fixtures/codemem/symbol_ids .python_sample.py#Bar.qux",
    "codemem tests/fixtures/codemem/symbol_ids #python_sample.py#Outer",
    "codemem tests/fixtures/codemem/symbol_ids #python_sample.py#Outer#Inner",
]
```

Tests MUST assert **exact string equality** on the emitted set. Any parser change that alters an ID is an implicit schema migration (may require `codemem migrate-symbol-ids` data migration, per plan §10 M1 risk #3 mitigation).

---

## Open questions (for v2+)

- **Method resolution order on inherited methods** — do we emit an ID for the inherited method on the subclass, or only on the base class? (v1: only on defining class; callers of the inherited method form edges to the base-class ID.)
- **Re-exports** — `from foo import bar as baz` produces `baz` in the importing file. v1 treats the importing site as an edge, not a new symbol. Revisit if needed.
- **Deleted file survivors** — when a file is removed, FK CASCADE drops all its symbols + edges. If external consumers have cached IDs, they dangle. v1 accepts this; v2 may add tombstones.

---

**End of grammar. Apply as v1 for M1; revisions require schema version bump + `migrate-symbol-ids` utility (per M1 risk #3 mitigation in plan).**
