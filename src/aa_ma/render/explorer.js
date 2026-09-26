// The explorer's drill script (diagram-generation M12, map Ticket 11). Embedded verbatim
// as the page's one inline script element, hashed into its CSP by explorer.py. The pure
// functions are the JS twin of codemem.draw (node_id, collapse, escape_label); the shared
// fixture tests/fixtures/draw-node-ids.json pins them to the Python, and
// tests/render/explorer_contract.test.mjs runs them under `node --test`.
'use strict';

// codemem.draw.cut.node_id: seed 7, h*31 + c, uint32, base36 over `L<level>:<name>`;
// c = charCodeAt(0) of each code point (the high surrogate beyond the BMP).
function nid(name, level) {
  let h = 7;
  for (const ch of `L${level}:${name}`) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return 'n' + h.toString(36);
}

// codemem.draw.cut.collapse: L0 keeps 1 directory segment, L1 keeps 2; L2 is the file.
function collapse(path, level) {
  if (level >= 2) return path;
  return path.split('/').slice(0, -1).slice(0, level + 1).join('/') || path;
}

function isTest(path) {
  return path.split('/').slice(0, -1).includes('tests');
}

// codemem.draw.mermaid.escape_label: '#' first; '%{}' stop a smuggled %%{init}%%; '`'
// blocks markdown-string mode; anything unprintable becomes '?' (Python's str.isprintable).
// Pinned by tests/fixtures/draw-label-rules.json. Known gap: code points assigned after
// Unicode 15.1 are unprintable to Python 3.13 but printable here — graphic, not a risk.
const UNPRINTABLE = /[\p{C}\p{Zl}\p{Zp}]|[^\S ]/gu;
const ENTITIES = [['#', '#35;'], ['"', '#quot;'], ['<', '#lt;'], ['>', '#gt;'],
  ['%', '#37;'], ['{', '#123;'], ['}', '#125;'], ['`', '#96;']];
function escapeLabel(text) {
  for (const [raw, entity] of ENTITIES) text = text.split(raw).join(entity);
  return text.replace(UNPRINTABLE, '?');
}

// A path shown as plain text (textContent): no markup risk, but controls and bidi overrides
// could still spoof what the reader sees.
function displayPath(text) {
  return text.replace(UNPRINTABLE, '?');
}

// The pinned mermaid renders a flowchart node as <g class="node" id="<renderId>-flowchart-<nid>-<i>">
// (no data-id) — proven by the M12.1 prototype against the real SVG.
function nodeIdOf(elementId) {
  const m = /(?:^|-)flowchart-(n[0-9a-z]+)-\d+$/.exec(elementId || '');
  return m ? m[1] : null;
}

// One level of the embedded graph as mermaid text, plus the id -> name lookup the click
// handler needs. A scope ending in '/' is a directory (prefix); otherwise one file (exact).
// Deterministic: nodes and edges sorted by name (UTF-16 order — codemem sorts by code point,
// so the two can differ only for names beyond the BMP). Throws on a node-id collision.
function compute(graph, { level, scope, tests }) {
  const hit = (p) => (scope.endsWith('/') ? p.startsWith(scope) : p === scope);
  const edges = new Map();
  for (const [src, dst, kind] of graph.edges) {
    if (!tests && (isTest(src) || isTest(dst))) continue;
    if (scope && !hit(src) && !hit(dst)) continue;
    const a = collapse(src, level);
    const b = collapse(dst, level);
    if (a !== b) edges.set(`${a}\u0000${b}\u0000${kind}`, [a, b, kind]);
  }
  const all = [...edges].sort(([k1], [k2]) => (k1 < k2 ? -1 : 1)).map(([, e]) => e);
  const kept = all.slice(0, graph.maxEdges);
  const lookup = new Map();
  for (const [a, b] of kept) {
    for (const n of [a, b]) {
      const id = nid(n, level);
      const seen = lookup.get(id);
      if (seen !== undefined && seen !== n) throw new Error(`node id collision: ${id} is both ${seen} and ${n}`);
      lookup.set(id, n);
    }
  }
  const lines = ['flowchart LR'];
  if (all.length > kept.length) lines.push(`%% ${all.length - kept.length} edges not shown: over mermaid maxEdges ${graph.maxEdges}`);
  for (const [id, n] of [...lookup].sort((x, y) => (x[1] < y[1] ? -1 : 1))) lines.push(`  ${id}["${escapeLabel(n)}"]`);
  for (const [a, b, kind] of kept) lines.push(`  ${nid(a, level)} -->|"@${kind}"| ${nid(b, level)}`);
  return { text: lines.join('\n') + '\n', lookup, edges: kept.length };
}

if (typeof module !== 'undefined') module.exports = { nid, collapse, isTest, escapeLabel, displayPath, nodeIdOf, compute };

if (typeof document !== 'undefined') {
  const G = JSON.parse(document.getElementById('graph').textContent);
  const $ = (id) => document.getElementById(id);
  if (G.stale) { $('stale').hidden = false; $('stale').textContent = `Index is stale — ${G.stale}. Showing the graph as last indexed.`; }
  const files = new Set(G.edges.flatMap(([src, dst]) => [src, dst]));
  const trail = [{ level: 0, scope: '' }];
  let lookup = new Map(); // always the lookup of the SVG currently in #out
  let seq = 0;
  async function draw() {
    const mine = ++seq; // a newer draw() supersedes this one, even mid-render
    const view = trail[trail.length - 1];
    const out = $('out');
    $('up').disabled = trail.length === 1;
    let r;
    try {
      r = compute(G, { ...view, tests: $('tests').checked });
    } catch (e) {
      lookup = new Map();
      out.textContent = e.message;
      return;
    }
    $('where').textContent = `L${view.level}${view.scope ? ' · ' + displayPath(view.scope) : ''} · ${r.lookup.size} nodes · ${r.edges} edges`;
    if (!r.edges) { lookup = new Map(); out.textContent = 'No edges at this level.'; return; }
    try {
      const { svg } = await mermaid.render(`explorer-${mine}`, r.text);
      if (mine !== seq) return; // stale: a later view is already drawn or drawing
      out.innerHTML = svg; // mermaid output under securityLevel "strict" (DOMPurify-sanitised)
      lookup = r.lookup;
    } catch (e) {
      if (mine !== seq) return;
      lookup = new Map();
      out.textContent = `mermaid could not render this view: ${e.message}`;
    }
  }
  // One delegated listener, attached once: it survives every re-render of #out.
  $('out').addEventListener('click', (e) => {
    const g = e.target.closest('g.node');
    const name = g && lookup.get(nodeIdOf(g.id));
    if (!name) return;
    // A directory drills one level down inside it; a file shows its own neighbourhood.
    const { level } = trail[trail.length - 1];
    trail.push(files.has(name) ? { level: 2, scope: name } : { level: level + 1, scope: name + '/' });
    draw();
  });
  $('up').addEventListener('click', () => { if (trail.length > 1) { trail.pop(); draw(); } });
  $('top').addEventListener('click', () => { trail.length = 1; draw(); });
  $('tests').addEventListener('change', draw);
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", maxEdges: G.maxEdges,
    theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default' });
  draw();
}
