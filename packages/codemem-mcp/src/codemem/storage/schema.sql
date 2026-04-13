-- codemem SQLite schema v1 (M1 Task 1.2)
--
-- PRAGMAs and DDL pinned per codemem-reference.md §Storage. Three-table
-- canonical model: files, symbols, edges. Cross-file edges carry a
-- dst_unresolved column so unresolved imports/calls are still persisted
-- (distinguishing "dead link" from "not yet resolved").
--
-- This file is applied by storage.db._apply_schema() on a fresh DB. The
-- migration framework (PRAGMA user_version + MIGRATIONS list in db.py)
-- bumps this to v2 in M3 when commits/ownership/co_change_pairs land.

-- ---------------------------------------------------------------------
-- PRAGMAs (persisted)
-- ---------------------------------------------------------------------
PRAGMA application_id = 1129137485;   -- 0x434D454D ('CMEM' ASCII), identifies codemem DBs
PRAGMA journal_mode = WAL;            -- Concurrent readers during writer
PRAGMA user_version = 1;              -- Schema version — M1

-- ---------------------------------------------------------------------
-- Files — one row per tracked source file
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS files (
    id              INTEGER PRIMARY KEY,
    path            TEXT    NOT NULL UNIQUE,       -- repo-relative
    lang            TEXT    NOT NULL,              -- 'python','typescript',...
    mtime           INTEGER,
    size            INTEGER,
    content_hash    TEXT,                          -- SHA-256 hex
    last_indexed    INTEGER NOT NULL               -- unix epoch seconds
);

CREATE INDEX IF NOT EXISTS idx_files_lang ON files(lang);

-- ---------------------------------------------------------------------
-- Symbols — one row per extracted definition (function/class/method/...)
-- ---------------------------------------------------------------------
-- SCIP-shaped ID per docs/codemem/symbol-id-grammar.md. See reference.md.
CREATE TABLE IF NOT EXISTS symbols (
    id              INTEGER PRIMARY KEY,
    file_id         INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    scip_id         TEXT    NOT NULL,              -- e.g. 'codemem packages/codemem-mcp/src/codemem /storage/db.py#init_db'
    name            TEXT    NOT NULL,              -- unqualified symbol name
    kind            TEXT    NOT NULL,              -- function|class|method|var|import|...
    line            INTEGER,
    signature       TEXT,                          -- canonicalized signature for display
    signature_hash  TEXT,                          -- hash of normalized signature, used by M2 diff
    docstring       TEXT,
    parent_id       INTEGER REFERENCES symbols(id) ON DELETE CASCADE,  -- e.g. method.parent = class
    UNIQUE(file_id, scip_id)
);

CREATE INDEX IF NOT EXISTS idx_symbols_file_kind_name ON symbols(file_id, kind, name);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);

-- ---------------------------------------------------------------------
-- Edges — directed relationships between symbols
-- ---------------------------------------------------------------------
-- kind: 'call' | 'import' | 'inherit'
-- Either dst_symbol_id (resolved) OR dst_unresolved (string target) is set.
-- Allowing NULL on dst_symbol_id lets us persist unresolved imports so that
-- resolution can happen lazily or be retried when more files are indexed.
CREATE TABLE IF NOT EXISTS edges (
    src_symbol_id   INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    dst_symbol_id   INTEGER          REFERENCES symbols(id) ON DELETE CASCADE,
    dst_unresolved  TEXT,                          -- e.g. 'requests.get' when 'requests' not indexed
    kind            TEXT    NOT NULL,              -- 'call'|'import'|'inherit'
    PRIMARY KEY(src_symbol_id, kind, dst_symbol_id, dst_unresolved),
    CHECK (dst_symbol_id IS NOT NULL OR dst_unresolved IS NOT NULL)
);

-- Covering indexes per codemem-reference.md §Storage. The recursive CTE
-- in reference.md § "Canonical Recursive CTE" needs idx_edges_dst for
-- who_calls/blast_radius traversal (dst → src direction).
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_symbol_id, kind, src_symbol_id);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_symbol_id, kind, dst_symbol_id);
