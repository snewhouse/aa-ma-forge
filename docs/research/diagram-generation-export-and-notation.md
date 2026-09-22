# SVG/PNG export and non-mermaid notation for the onboarding diagram effort

**Created:** 2026-09-22
**Author:** Claude (aa-ma-researcher), charting effort diagram-generation Ticket 13
**Reviewed-Through-Date:** 2026-09-22
**Valid-Through:** 2026-Q4 (invalidated by: mermaid-cli shipping mermaid 12; GitHub or the Artifact viewer bumping their bundled mermaid; D2 gaining native GitHub render)
**Sources:**
- <https://github.com/mermaid-js/mermaid/releases/tag/mermaid%4012.0.0> — mermaid 12.0.0 (2026-09-10) bundles ELK as the **default** layout; ES2024/Node 22.12+; "mermaid requires a browser"; IIFE build grows ~500 kB gzipped
- <https://mermaid.js.org/config/layouts.html> — elk (default) / dagre / cose-bilkent / tidy-tree; which diagram types use ELK; tiny build omits it
- <https://github.com/mermaid-js/mermaid-cli> + <https://raw.githubusercontent.com/mermaid-js/mermaid-cli/master/src/index.js> — mmdc options (`-e svg|png|pdf`, `-I/--svgId` default `my-svg`, `-p/--puppeteerConfigFile`, `--iconPacks` fetched from unpkg)
- <https://registry.npmjs.org/@mermaid-js/mermaid-cli> — v11.17.0 (2026-09-02), MIT, `engines.node ^18.19 || >=20`, **peerDependency `puppeteer: ^23 || ^24 || ^25`**, `dependencies.mermaid ^11.14.0`
- <https://github.com/mermaid-js/mermaid-cli/blob/master/docs/linux-sandbox-issue.md> and `.../already-installed-chromium.md` — `--no-sandbox` via puppeteer-config.json; `executablePath`; `PUPPETEER_SKIP_DOWNLOAD=1`
- <https://pptr.dev/guides/configuration> — puppeteer downloads Chrome on install, cached in `~/.cache/puppeteer`
- <https://registry.npmjs.org/mermaid-isomorphic> — v3.1.0, MIT, peerDependency `playwright: 1`
- <https://github.com/jihchi/mermaid.ink> — self-host = Docker + headless Chrome (`--cap-add=SYS_ADMIN` "not recommended", seccomp workarounds)
- <https://docs.kroki.io/kroki/setup/encode-diagram/> — GET requests carry the diagram **source** deflate+base64 in the URL
- <https://docs.kroki.io/kroki/setup/install/> — mermaid needs the extra `yuzutech/kroki-mermaid` companion container; <https://kroki.io/> — D2 supported, **svg only**
- <https://d2lang.com/tour/exports> — "PNG exports have no external dependencies. D2 renders them directly, unlike Mermaid, which uses a headless browser like Chromium"; SVG gets "a deterministic hash prefix"
- <https://d2lang.com/tour/layouts/> and <https://d2lang.com/tour/tala> — dagre (default) / ELK / TALA; TALA-only keywords; TALA "Has randomness"
- <https://github.com/d2lang/d2> — MPL-2.0, v0.9.0 (2026-09-07), active; `docs/examples/flipt/input.d2` — real published example
- <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams> — GitHub renders mermaid, GeoJSON, TopoJSON, ASCII STL. No D2.
- <https://code.visualstudio.com/updates/v1_121> — VS Code 1.121 (2026-05-20) ships built-in **Mermaid** Markdown/notebook preview with pan+zoom
- <https://mermaid.js.org/syntax/architecture.html> (source: `packages/mermaid/src/docs/syntax/architecture.md`) — `architecture-beta`, fcose layout, `seed` default 1, overlap limitation issue #6120
- <https://mermaid.js.org/syntax/block.html> — block diagrams use fixed manual columns, not auto-layout
- Repo: `docs/adr/0010-architecture-views-and-render.md:31-43` (drivers), `:92-99` (render + mmdc seam); `src/aa_ma/render/mermaid_lint.py:30-40` (`KNOWN_TYPES`), `:302-331` (`render_check`, `MMDC_BIN`); `src/aa_ma/render/html.py:12` (mermaid pin 11.17.2); `claude-code/commands/aa-ma-share.md:13-15` (publish markdown, never HTML)

## Answer

**(a)** There is **no browser-free mermaid renderer** — mermaid's own 12.0.0 release note says "mermaid requires a browser", and every path (mmdc/puppeteer, mermaid-isomorphic/playwright, mermaid.ink, kroki-mermaid) puts Chromium underneath. `mmdc` is the only option that is fully offline, MIT, and already respects the no-new-runtime-dep rule — the forge shells out to it through the `MMDC_BIN` seam today (`mermaid_lint.py:307`) and it is a Node dev dependency, never an `aa_ma` one. Hosted mermaid.ink / kroki.io send your diagram source off the machine (kroki GET puts it in the URL); for a private repo's architecture that is a plain leak and should stay out of scope. mmdc output is *reproducible enough* for a `--check` (fixed `--svgId` default `my-svg`, no RNG in the id path) but is **not** promised byte-stable across mermaid/Chromium versions — pin both or compare structurally, not by hash.

**(b)** The premise that D2 lays out better than mermaid expired 12 days ago. **mermaid 12.0.0 (2026-09-10) bundles ELK and makes it the default** for flowcharts — the same ELK engine D2 offers as its non-default option. At 13–40 layered nodes that closes the gap that ADR-0010's "❌ Go binary required" trade-off was paying for. D2 keeps exactly one real technical edge (browser-free PNG) and one real layout edge (TALA's per-container `direction`, `top`/`left` position locks, container-first routing) — but TALA is Terrastruct's own engine, self-described as having "randomness", and D2 renders in **none** of the three places the onboarding reader already is: GitHub markdown, VS Code preview, Artifact viewer. Excalidraw is a scene JSON, not a derivable text notation — wrong tool for a graph you generate. Within mermaid, `architecture-beta` is **not** the L0/L1 answer (fcose force layout, documented overlap bug #6120 that tuning cannot fix) and `block` is manual column positioning (hand-maintained coordinates over a derived graph). Stay on `flowchart` + `subgraph`.

**(c)** Admitting D2 breaks two of ADR-0010's five decision drivers outright ("renders where plans are read", "no new runtime dependency" in spirit) and weakens a third. It is a **superseding ADR**, not an amendment — but you do not need one, because the layout motive is gone.

## (a) Mermaid → SVG/PNG

| Option | Needs | Offline | Deterministic | Licence | Respects "no new runtime dep for `aa_ma`" |
|---|---|---|---|---|---|
| `@mermaid-js/mermaid-cli` (`mmdc`) 11.17.0 | Node `^18.19 \|\| >=20`; peerDep `puppeteer ^23–^25` → Chrome downloaded to `~/.cache/puppeteer`; on Linux/WSL may need `-p puppeteer-config.json` with `--no-sandbox` | ✅ once installed — **except** `--iconPacks`, which fetches from unpkg at render time | Reproducible per pinned (mermaid, Chromium) pair: `--svgId` defaults to the constant `my-svg`, no RNG in ids. Byte-stability across versions **not promised** | MIT | ✅ Node-side dev tool; already behind the `MMDC_BIN` seam and the `UNKNOWN`-never-`PASS` rule (`mermaid_lint.py:302-331`) |
| `mmdc` via `minlag/mermaid-cli` Docker/Podman image | Docker or Podman; `-v … :/data`; Podman needs `--userns keep-id` + `:z` | ✅ after pull | Better than host install — image pins mermaid+Chromium together | MIT | ✅ (nothing enters `uv sync`) |
| `mermaid-isomorphic` 3.1.0 + Playwright | Node; peerDep `playwright: 1` (its own browser download) | ✅ | Same class as mmdc; no CLI, you write the driver | MIT | ✅ but strictly worse than mmdc: more code for the same Chromium |
| Public **mermaid.ink** | HTTPS only | ❌ | n/a | see repo LICENSE | ❌ on privacy, not on deps: **diagram source leaves the machine** (base64 in the URL) |
| Self-hosted mermaid.ink | Docker + headless Chrome; README calls `--cap-add=SYS_ADMIN` "not recommended", suggests a seccomp profile instead | ✅ | n/a | as repo | ⚠️ a service to operate, for one SVG |
| Public **kroki.io** | HTTPS only | ❌ | n/a | Apache-2.0 (project) | ❌ **source travels in the URL** (deflate+base64, per the Encode Diagrams page) |
| Self-hosted Kroki | `yuzutech/kroki` **plus** the separate `yuzutech/kroki-mermaid` container (mermaid needs its own browser) | ✅ | n/a | Apache-2.0 | ⚠️ two containers; only worth it if you already run Kroki |
| Browser-free mermaid renderer (pure Python / pure Node) | — | — | — | — | **Not found.** mermaid 12.0.0's own release note: "as mermaid requires a browser". D2's docs make the same observation about mermaid. |
| `d2` CLI (different notation, listed for contrast) | one static Go binary | ✅ | SVG ids use "a deterministic hash prefix"; TALA layout "has randomness" | MPL-2.0 | ✅ on deps — **but** it is not mermaid (see (b)/(c)) |

**The one asymmetry worth naming:** `d2 in.d2 out.png` needs no browser at all; every mermaid→PNG path needs Chromium. If byte-stable, browser-free raster export ever becomes a hard requirement, that is the *only* reason to reopen notation.

## (b) Notation comparison

| | Layout engine(s) | Edge routing / labels | Containers | Deterministic | GitHub native | VS Code native |
|---|---|---|---|---|---|---|
| mermaid `flowchart`, mermaid **11.x** (repo pins 11.17.2) | dagre (default); ELK via `layout: elk` + the separate `@mermaid-js/layout-elk` package | dagre: layered, orthogonal-ish; label collision is the usual 20+ node complaint | `subgraph` (nestable) | yes (no RNG) | ✅ | ✅ (1.121+) |
| mermaid `flowchart`, mermaid **12.0.0** (2026-09-10) | **ELK bundled and default**; `elk.stress/force/mrtree/sporeOverlap/box/rectpacking` variants; `layout: dagre` to opt out | ELK layered routing — fewer overlaps on "large or intricate diagrams" (mermaid's own wording) | `subgraph` | yes | ✅ *when GitHub bumps* — version not controlled by us | ✅ *when VS Code bumps* |
| mermaid `architecture-beta` | fcose (force-directed), `seed` default `1` | edge sides pinned via `:L/:R/:T/:B`; **known overlap bug #6120 that the tuning knobs explicitly cannot fix** | `group … in parent` (nestable) | yes at `seed: 1`; `seed: 0` opts into `Math.random` | ✅ (11.1.0+) | ✅ |
| mermaid `block` | none — author writes `columns n` and places blocks | manual | yes | trivially | ✅ | ✅ |
| **D2** v0.9.0 | dagre (default), ELK, TALA | TALA: per-container `direction`, `top`/`left` locks, dynamic label positioning, routed grid-cell connections — none available on dagre/ELK | first-class, and the only engine with full container support is TALA | SVG hash prefix deterministic; **TALA "has randomness — a small change to a label can cascade into an entirely different layout"** | ❌ | ❌ built-in; ✅ via `d2lang/d2-vscode` (329★) |
| **Excalidraw** | n/a (hand-placed scene JSON) | manual | manual | n/a | ❌ | ❌ built-in |

**What the real published examples show.** D2's own documentation site (`d2lang/d2-docs`, Docusaurus, diagrams generated in CI) is the flagship D2 deployment; the largest *real-system* example the project ships is `docs/examples/flipt/input.d2` — Flipt's build/test/release pipeline, 94 lines, **11 containers**, only 7 top-level edges, and it leans heavily on `classes:`, `grid-block` sizing, `shape: image` icons and explicit `direction: right`. That is the honest picture: D2 looks best when an author hand-tunes styling and containers, which is the opposite of a *derived* graph with authored captions. Conversely this repo already ships a mermaid `flowchart LR` at the low end of your band — `docs/adr/0010-architecture-views-and-render.md:153-190`, **16 nodes / 12 edges / 4 subgraphs** — and it renders on GitHub with zero toolchain. Kroki's own gallery confirms the ceiling on D2's reach: it lists D2 as **svg only** while mermaid gets the full treatment. No published documentation site was found that ships D2 for a 13–40-node *onboarding* view; the adopters found (JetBrains Writerside, Jamdesk) are tools that *support* D2, not docs that use it at that scale — treat those as secondary.

**On `architecture-beta` and `block` for L0/L1.** Neither helps. `architecture-beta` is aimed at cloud/CI service topologies, wants an icon per node (5 built-ins, else register an iconify pack — and mmdc's `--iconPacks` fetches from unpkg, breaking offline), and carries an overlap defect the docs say the spacing knobs will not resolve. `block` gives you fixed columns — you would be hand-maintaining coordinates for a graph the tool derives, which reintroduces exactly the drift ADR-0010 exists to prevent. `flowchart` + `subgraph` + (later) `layout: elk` is the right primitive at every zoom level, and it is the only one with a real click-through story (`click … href`) for the L0→L1→L2 navigation.

## (c) Cost under ADR-0010

ADR-0010's five drivers (`:31-43`) and how a second notation fares:

| Driver | D2 verdict |
|---|---|
| Cold-executability | neutral |
| No drift (text, checkable) | neutral — D2 is text too |
| **No new runtime dependency** | technically survivable (Go binary, not in `uv sync`) but the *rendered* artefact now requires a toolchain the reader does not have |
| **Renders where plans are read** | **broken.** GitHub renders mermaid/GeoJSON/TopoJSON/STL — not D2. VS Code 1.121's built-in preview is mermaid-only. The Artifact viewer renders mermaid. |
| Do not punish small plans | **broken.** Two notations = two lints, two rendering paths, two sets of authoring rules for LLM-authored diagrams that already have real syntax-error rates |

Concretely, admitting D2 would require:

1. `mermaid_lint.py` — `KNOWN_TYPES` (`:30-40`) is a *policy* allowlist of first-lines inside a ```` ```mermaid ```` fence. D2 is a different fence info-string, so this is not one tuple entry: it needs fence-language dispatch, a second `render_check` (a `D2_BIN` seam mirroring `MMDC_BIN`), and a second `UNKNOWN`-never-`PASS` rule. The `STALE_PATH` label scanner (`:153-168`) assumes mermaid `[...]` label syntax and would need a D2 parser.
2. `html.py` — the self-contained HTML ships one SRI-pinned mermaid script (`:12`, 11.17.2). D2 has no browser ESM equivalent you can SRI-pin the same way; you would have to **pre-render D2 to inline SVG at build time**, which makes the HTML no longer derivable from markdown alone and puts a Go binary on the render path.
3. `/aa-ma-share` — the command's whole premise (`aa-ma-share.md:13-15`) is "publish the markdown; the viewer renders mermaid natively; never render to HTML first". A D2 fence in a shared plan renders as a **code block**. There is no fix inside this design.
4. Spec/rules/templates — §13 says "mermaid, text-only" (`:60`); element #13, the `Diagram-Waiver` enum and Angle 6 all assume one notation.

**Amendment or supersession:** supersession. ADR-0010's Decision Outcome names the notation in its first bullet and its "Considered Options" already rejected D2 with a stated reason; reversing that reason is a new decision, not a clarification. An *amendment* is appropriate only for the narrow, non-contradictory case: adding "optional raster export via the existing `mmdc` seam" to the Rendering bullet (`:92-99`), which changes no driver.

**The cheap change that actually was in scope and is now outdated:** `html.py:12` pins mermaid 11.17.2 (dagre default). Bumping to 12.0.0 gets ELK layout for free in the self-contained HTML — but it is a **breaking** release (ES2024/Safari 17.4+), it re-lays-out and recolours every existing diagram, and the single-file IIFE build "grows by roughly 500 kB gzipped" because ELK is inlined. Note also that `mmdc` 11.17.0 still depends on `mermaid ^11.14.0`, so the lint's render check and the HTML would disagree on layout until mermaid-cli ships 12. That divergence is the real reason to treat the bump as its own decision.

## Recommendation

**Ship in v1 (onboarding audience, ranked by benefit/cost):**

1. **Mermaid only, `flowchart` + `subgraph`, at every zoom level.** It is the only notation that renders in all three places a new developer will open the artefact — GitHub, VS Code 1.121+, Artifact viewer — with nothing installed. Cost: zero. This is also what makes `click … href` L0→L1→L2 navigation work in the self-contained HTML.
2. **Keep the self-contained HTML as the primary deliverable, mermaid still pinned at 11.17.2.** Do not bump to 12 inside this effort: breaking, re-lays-out every existing diagram, +~500 kB gzipped, and mmdc would disagree with it. File a separate one-milestone decision.
3. **Optional `--svg` / `--png` export through the existing `MMDC_BIN` seam.** Reuse `render_check`'s discipline verbatim: absent or failing-for-a-non-parse-reason ⇒ `UNKNOWN`, never silent success. Document the WSL/Linux escape hatches (`-p puppeteer-config.json` with `--no-sandbox`; `PUPPETEER_SKIP_DOWNLOAD=1` + `executablePath` to reuse a system Chrome). Do **not** use `--iconPacks` — it phones unpkg. This is an ADR-0010 *amendment* at most.
4. **Explicitly rule out hosted renderers** (mermaid.ink, kroki.io) in the plan text, with the reason stated plainly: the diagram source — your private repo's architecture — travels to a third party, in the URL.

**Possible later:**

5. **Bump to mermaid 12 / opt into `layout: elk`** once mermaid-cli ships a mermaid-12 line, so lint and HTML agree. Then re-measure a 40-node L1 view before and after; if ELK fixes the label collisions, that is the whole layout question closed without leaving mermaid. *Cheapest remaining layout win.*
6. **D2 as an export target only** (`d2` reads a generated `.d2`, emits browser-free PNG/PDF/PPTX) **if and only if** a print/poster artefact becomes a requirement. Keep markdown+mermaid as the source of truth; a second *authoring* notation still needs a superseding ADR.
7. **Never Excalidraw as a source format.** If a hand-drawn look is ever wanted, `excalidraw/mermaid-to-excalidraw` (MIT, 886★) converts *from* mermaid — one-way, cosmetic, no new source of truth.

## Not pursued

- GitHub's exact bundled mermaid version — the GitHub docs deliberately don't publish one and tell you to run `info` in a fence; unverifiable without an authenticated render. Affects when finding #5 pays off.
- Whether the Claude Artifact viewer's mermaid version supports `architecture-beta` or `layout: elk` — no primary source; would need an empirical probe.
- Empirical byte-stability test of `mmdc` across two runs / two Chromium builds — would need an install, which the task forbade.
- Measured render time and output size of a 40-node flowchart under dagre vs ELK — needs mermaid 12 installed.
- Graphviz/DOT and PlantUML as third options — not in the question; both also fail the "renders on GitHub" driver.
- Structurizr/C4 — already rejected in ADR-0010 option C; `mermaid_lint.py` `KNOWN_TYPES` already allows mermaid's `C4Context/C4Container/C4Component`, which was not re-examined here.
- Kroki's licence text and public-instance retention policy — install docs are silent; only the URL-encoding mechanism was verified.
- Secondary write-ups found for D2 (LogRocket, Code4IT, personal blogs) — deliberately not cited; none trace to a primary layout benchmark.
