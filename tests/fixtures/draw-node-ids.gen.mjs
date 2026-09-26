// Generates tests/fixtures/draw-node-ids.json — the contract shared by codemem's Python
// emitter (draw/cut.py::node_id, ::collapse) and the explorer's JS (src/aa_ma/render/explorer.js).
// The hash and the collapse rule come from explorer.js itself — one JS copy; the Python side is
// checked against the output (tests/codemem/test_draw_cut.py, tests/render/test_explorer_fixture.py).
// nid: seed 7, h = h*31 + c, uint32, base36, where `c` is charCodeAt(0) of each CODE POINT
// (the high surrogate beyond the BMP) — the Python port matches that quirk, never "fixes" it.
// L2 rows also carry `collapse: [L0, L1]` (M12 §6.8: regenerating must not drop the pins).
// Run: node tests/fixtures/draw-node-ids.gen.mjs < keys.json > tests/fixtures/draw-node-ids.json
import { createRequire } from 'node:module';

const { nid, collapse } = createRequire(import.meta.url)('../../src/aa_ma/render/explorer.js');
let buf = '';
process.stdin.on('data', (d) => (buf += d));
process.stdin.on('end', () => {
  const keys = JSON.parse(buf); // [[level, name], ...]
  const out = keys.map(([level, name]) => ({
    level, name, id: nid(name, level), ...(level === 2 && { collapse: [collapse(name, 0), collapse(name, 1)] }),
  }));
  process.stdout.write(JSON.stringify(out, null, 1) + '\n');
});
