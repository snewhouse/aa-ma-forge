"""PROTOTYPE (Ticket 3, charting diagram-generation) — throwaway.

Dumps codemem's resolved call edges to JSON for the HTML demo.
Run: uv run python prototype/diagram-generation-3/extract.py > prototype/diagram-generation-3/graph.json
"""
import json, sqlite3, sys
from pathlib import Path

db = Path(".codemem/index.db")
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = conn.execute("""
    SELECT sf.path, s.name, df.path, d.name
      FROM edges e
      JOIN symbols s ON e.src_symbol_id = s.id JOIN files sf ON s.file_id = sf.id
      JOIN symbols d ON e.dst_symbol_id = d.id JOIN files df ON d.file_id = df.id
     WHERE e.kind = 'call'
""").fetchall()
files = [r[0] for r in conn.execute("SELECT path FROM files ORDER BY path")]
json.dump({"files": files, "edges": [list(r) for r in rows]}, sys.stdout)
