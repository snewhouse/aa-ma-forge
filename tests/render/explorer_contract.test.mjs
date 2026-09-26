// explorer_contract.test.mjs — the explorer's JS agrees with codemem's Python
// (diagram-generation M12, map Ticket 11). Run: node --test tests/render/explorer_contract.test.mjs
// The shared fixture pins node-id derivation and the directory-collapse rule; the page
// test reads the built HTML from EXPLORER_HTML (the CI job builds it first).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const X = require('../../src/aa_ma/render/explorer.js');
const rows = JSON.parse(readFileSync(new URL('../fixtures/draw-node-ids.json', import.meta.url), 'utf8'));

test('node ids match the shared fixture (every level)', () => {
  const bad = rows.filter((r) => X.nid(r.name, r.level) !== r.id);
  assert.deepEqual(bad, []);
});

test('directory collapse matches the shared fixture', () => {
  const pinned = rows.filter((r) => r.collapse);
  assert.ok(pinned.length > 0);
  const bad = pinned.filter((r) => X.collapse(r.name, 0) !== r.collapse[0] || X.collapse(r.name, 1) !== r.collapse[1]);
  assert.deepEqual(bad, []);
});

const G = {
  maxEdges: 500,
  edges: [
    ['src/aa_ma/a.py', 'src/aa_ma/b/c.py', 'import'],
    ['packages/x/y.py', 'src/aa_ma/a.py', 'call'],
    ['tests/t.py', 'src/aa_ma/a.py', 'import'],
  ],
};
const names = (r) => new Set(r.lookup.values());

test('compute derives a different node set per level (AC2b)', () => {
  const l0 = X.compute(G, { level: 0, scope: '', tests: false });
  const l2 = X.compute(G, { level: 2, scope: '', tests: false });
  assert.deepEqual(names(l0), new Set(['src', 'packages']));
  assert.deepEqual(names(l2), new Set(['src/aa_ma/a.py', 'src/aa_ma/b/c.py', 'packages/x/y.py']));
});

test('edges carry their kind as a quoted sigil, like codemem draw', () => {
  const r = X.compute(G, { level: 2, scope: '', tests: false });
  assert.match(r.text, new RegExp(`${X.nid('src/aa_ma/a.py', 2)} -->\\|"@import"\\| ${X.nid('src/aa_ma/b/c.py', 2)}`));
  assert.match(r.text, /-->\|"@call"\|/);
});

test('tests are hidden unless asked for', () => {
  assert.ok(!names(X.compute(G, { level: 2, scope: '', tests: false })).has('tests/t.py'));
  assert.ok(names(X.compute(G, { level: 2, scope: '', tests: true })).has('tests/t.py'));
});

test('a scope keeps only edges touching it', () => {
  const r = X.compute(G, { level: 2, scope: 'packages/', tests: false });
  assert.deepEqual(names(r), new Set(['packages/x/y.py', 'src/aa_ma/a.py']));
});

test('edges beyond maxEdges are dropped and said so', () => {
  const many = { maxEdges: 2, edges: [['a/1.py', 'b/1.py', 'import'], ['a/2.py', 'b/2.py', 'import'], ['a/3.py', 'b/3.py', 'import']] };
  const r = X.compute(many, { level: 2, scope: '', tests: false });
  assert.equal(r.edges, 2);
  assert.match(r.text, /^%% 1 edges not shown/m);
});

test('labels cannot break out of the mermaid node', () => {
  const evil = 'a"]; click n call alert() %%{init: {}}%% <img src=x> `b`.py';
  const out = X.escapeLabel(evil);
  for (const ch of ['"', '<', '>', '%', '{', '}', '`']) assert.ok(!out.includes(ch), ch);
  assert.equal(X.escapeLabel('ok\u0007.py'), 'ok?.py');
});

test("a rendered node's element id maps back to its node id (prototype-proven scheme)", () => {
  assert.equal(X.nodeIdOf('m1790422753999-flowchart-n1wgktcl-2'), 'n1wgktcl');
  assert.equal(X.nodeIdOf('flowchart-n1wgktcl-0'), 'n1wgktcl');
  assert.equal(X.nodeIdOf('L-n1-n2-0'), null);
  assert.equal(X.nodeIdOf(''), null);
});

test('the built page: every inline script is hash-allowed by its CSP (AC3)', () => {
  const path = process.env.EXPLORER_HTML;
  assert.ok(path, 'set EXPLORER_HTML to a built explorer.html (the CI job builds it)');
  const page = readFileSync(path, 'utf8');
  const csp = page.match(/http-equiv="Content-Security-Policy" content="([^"]*)"/)[1];
  const scriptSrc = csp.split(';').find((d) => d.trim().startsWith('script-src'));
  assert.ok(!scriptSrc.includes("'unsafe-inline'"));
  const inline = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.equal(inline.length, 1);
  for (const body of inline) {
    const sha = createHash('sha256').update(body, 'utf8').digest('base64');
    assert.ok(scriptSrc.includes(`'sha256-${sha}'`), `inline script sha256-${sha} not in ${scriptSrc}`);
  }
  for (const m of page.matchAll(/<script src="([^"]+)"/g)) assert.ok(m[1].startsWith('https://cdn.jsdelivr.net/'), m[1]);
  assert.match(inline[0], /securityLevel: "strict"/);
});
