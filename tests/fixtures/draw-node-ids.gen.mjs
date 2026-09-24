// Generates tests/fixtures/draw-node-ids.json — the node-id contract shared by
// codemem's Python emitter (draw/cut.py::node_id) and M12's JS explorer.
// Hash ported verbatim from prototype/diagram-generation-3 (`nid`): seed 7, h = h*31 + c,
// uint32, base36 — where `c` is charCodeAt(0) of each CODE POINT (`[...s]`). For a
// non-BMP character that is its high surrogate only; the Python port must match that
// quirk, not "fix" it. The key hashed is `L<level>:<name>`.
// Run: node tests/fixtures/draw-node-ids.gen.mjs < keys.json > tests/fixtures/draw-node-ids.json
const nodeId = (name, level) =>
  'n' + [...`L${level}:${name}`].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7).toString(36);
let buf = '';
process.stdin.on('data', d => (buf += d));
process.stdin.on('end', () => {
  const keys = JSON.parse(buf);   // [[level, name], ...]
  const out = keys.map(([level, name]) => ({ level, name, id: nodeId(name, level) }));
  process.stdout.write(JSON.stringify(out, null, 1) + '\n');
});
