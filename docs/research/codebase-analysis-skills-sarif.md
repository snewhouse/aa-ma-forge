# What is the minimal valid SARIF 2.1.0 log a stdlib-only Python tool should emit so it validates against the OASIS schema and GitHub code scanning accepts it?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for charting effort `codebase-analysis-skills` (topic: sarif)
**Reviewed-Through-Date:** 2026-09-27 (OASIS spec + schema, github/docs source, github/codeql-action source and SchemaStore copy all fetched on this date)
**Valid-Through:** 2027-Q1 (invalidated by a SARIF 2.2 OASIS standard, a change to GitHub's "SARIF support" reference page, or codeql-action changing its vendored schema / fingerprint algorithm)
**Sources:**
- https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os-complete.html — SARIF 2.1.0 Plus Errata 01, OASIS Standard, 28 Aug 2023 (normative prose; section numbers below)
- https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json — normative JSON schema (Draft-04; sha256 `c3b4bb2d…682e`, 112,768 bytes as fetched)
- https://github.com/github/docs/blob/main/content/code-security/reference/code-scanning/sarif-files/sarif-support.md (last commit `ca68008` 2026-07-20) — rendered at https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning — GitHub's required/optional property tables, fingerprints, limits
- https://github.com/github/docs/blob/main/content/code-security/reference/code-scanning/sarif-files/troubleshoot-sarif-uploads/sarif-invalid.md — invalid SARIF is rejected
- https://github.com/github/codeql-action/blob/7b6a151fb55e03ce158c75249f8880ea01aabebf/src/upload-lib.ts — upload-sarif schema validation (L453-518) and fingerprint call (L635)
- https://github.com/github/codeql-action/blob/7b6a151fb55e03ce158c75249f8880ea01aabebf/src/fingerprints.ts — `primaryLocationLineHash` algorithm (L32-78, L141-174, L259-321)
- https://github.com/github/codeql-action/blob/7b6a151fb55e03ce158c75249f8880ea01aabebf/src/sarif-schema-2.1.0.json — the schema copy GitHub's action actually validates against
- https://json.schemastore.org/sarif-2.1.0.json — SchemaStore copy (Draft-07), the `$schema` URI in GitHub's examples; repo licence Apache-2.0 (https://github.com/SchemaStore/schemastore)
- https://github.com/oasis-tcs/sarif-spec/blob/main/LICENSE.md — OASIS IPR Policy, RF on RAND Terms Mode
- https://python-jsonschema.readthedocs.io/en/stable/validate/ — supported drafts; format checking off by default
- https://github.com/advanced-security/dismiss-alerts — how SARIF `suppressions` become dismissed alerts (not native)

## Answer

The schema floor is tiny: `{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"x"}}}]}` validates. Each result then needs only `message` with `text` (or `id`). GitHub asks for more, and marks these "Required": `$schema`, `runs[].results[]`, `driver.rules[]` with `id`/`shortDescription.text`/`fullDescription.text`/`help.text`, and per result `message.text`, `locations[0].physicalLocation.artifactLocation.uri` (a repo-relative path), `region.startLine/startColumn/endLine/endColumn` and `partialFingerprints`. Emit `ruleId` on every result as well. For identity, compute your own versioned `fingerprints` entry. Let `github/codeql-action/upload-sarif` fill in `partialFingerprints.primaryLocationLineHash`, which is the only identity key GitHub uses. The OASIS schema is Draft-04, and Python `jsonschema` 4.25.1 validates it with `Draft4Validator`. I checked the worked example below against it: VALID, plus 15 negative mutations INVALID.

## Evidence

### 1. Required fields — schema vs spec vs GitHub

| Field | OASIS schema | OASIS prose | GitHub code scanning |
|---|---|---|---|
| `version` = `"2.1.0"` | required, `enum ["2.1.0"]` (schema L16-20, L48) | SHALL, SHOULD appear first (§3.13.2) | Required, only 2.1.0 supported (sarif-support.md:125) |
| `$schema` | optional, `format: uri` (schema L10) | MAY; NOTE 2 names the errata01 schema URL (§3.13.3) | Required. Example given is `https://json.schemastore.org/sarif-2.1.0.json` (sarif-support.md:124) |
| `runs[]` | required (schema L48) | SHALL; `[]` if no data, `null` on failure (§3.13.4) | Required (sarif-support.md:126) |
| `run.tool.driver.name` | `run` requires `tool`, `tool` requires `driver`, `toolComponent` requires `name` (schema L2340, L2915/L2943, L2946/L3141) | SHALL (§3.18.2, §3.19.8) | Required (sarif-support.md:134, 143) |
| `run.results[]` | optional | — | Required (sarif-support.md:137) |
| `driver.rules[]` + `id`, `shortDescription.text`, `fullDescription.text`, `help.text` | only `reportingDescriptor.id` required (schema L1816/L1919) | — | all Required (sarif-support.md:146, 154, 156, 157, 159) |
| `result.message` | required; message needs `text` **or** `id` (`anyOf`, schema L1433, L1468-1476, L2036/L2282) | SHALL (§3.27.11) | `message.text` Required, shown as the alert title (sarif-support.md:176) |
| `result.ruleId` | optional string (schema L2042) | SHALL be present if `rule.id` is absent (§3.27.5) | Optional, but "has to be the same across analysis" (sarif-support.md:32, 172) |
| `result.ruleIndex` | integer ≥ -1, default -1 (schema L2047) | MAY. SHALL be absent unless the descriptor exists in `rules` (§3.27.6) | Optional (sarif-support.md:173) |
| `result.level` | `enum [none, note, warning, error]`, default `warning` (schema L2066) | `none` only when `kind` ≠ `fail` (§3.27.10) | Optional. Overrides the rule's `defaultConfiguration.level` (sarif-support.md:158, 175) |
| `locations[].physicalLocation.artifactLocation.uri` | `physicalLocation` anyOf `address`/`artifactLocation`; `uri` is `format: uri-reference` (schema L1608-1648, L291-303) | relative reference plus `uriBaseId` SHOULD (§3.4.3, §3.4.4) | Required. Repo-relative path recommended, e.g. `src/main.js`. Only the first location is used (sarif-support.md:177, 196, 72) |
| `region.startLine` | integer ≥ 1. Region anyOf `startLine`/`charOffset`/`byteOffset` (schema L1707-1790) | SHALL for line/column regions (§3.30.5) | `startLine`, `startColumn`, `endLine`, `endColumn` all Required (sarif-support.md:197-200) |

Things to watch for:
- The result object has `additionalProperties: false`. A bare `"confidence": "high"` on a result is rejected, so custom data must go under `properties` (verified below).
- GitHub says: "You must supply an explicit value for any property marked as "required". The empty string is not supported" (sarif-support.md:116). It also says "Any valid SARIF 2.1.0 output file can be uploaded, however, code scanning will only use the following supported properties" (sarif-support.md:118).
- GitHub's own "Example with minimum required properties" (sarif-support.md:236-292) contains a literal `...` and a trailing comma, so it is not valid JSON. Do not copy it verbatim.
- Hard upload limits (sarif-support.md:103-110 + `data/reusables/code-scanning/sarif-limits.md`): 10 MB gzip-compressed, 20 runs per file, 25,000 results per run.

### 2. Stable finding identity across runs

- **`fingerprints`** (§3.27.16): an object of string values. Each value "SHALL … be the same for all results that are logically identical", and should survive changes to the enlistment root or line number. Property names SHALL be *versioned hierarchical strings*, e.g. `"stableResultHash/v2"`. Consumers compare using the latest common version. Schema: object of strings (L2120).
- **`partialFingerprints`** (§3.27.17): strings that *contribute* to a fingerprint, which the result-management system then computes (Appendix B). Same versioned-name rule. Schema: object of strings (L2112).
- **GitHub uses only `partialFingerprints.primaryLocationLineHash`**: "Code scanning only uses the `primaryLocationLineHash`" (sarif-support.md:178). Other points from the same page:
  - `upload-sarif` computes it when it is missing (sarif-support.md:42, 178).
  - Direct `/code-scanning/sarifs` API uploads without it "may see duplicate alerts" (sarif-support.md:44).
  - Filepaths must be consistent across runs, or alerts are closed and re-opened (sarif-support.md:36).
- **Algorithm** (codeql-action `fingerprints.ts`):
  - A rolling hash (mod 37, `BLOCK_SIZE` 100) over the first 100 non-space/tab characters from the start of the primary location's `startLine`, with line endings normalised (L11-17, L32-43).
  - Emitted as `"<hex>:<occurrence-count>"` (L70-76).
  - It needs the source file on disk under the checkout (L188-254).
  - If you supply a value that differs from the computed one, the action logs a warning and **keeps yours** (L159-172).
  - Results without `region.startLine` are skipped (L286-289).
- **Recommendation for a stdlib-only tool:**
  1. Emit your own `fingerprints: {"<tool>Finding/v1": sha256(ruleId + repo-relative uri + normalised symbol/snippet)}`. This is the key your own baseline diffing uses.
  2. Omit `primaryLocationLineHash` when uploading via the `upload-sarif` action, which then computes it correctly. Only port the algorithm if you upload through the raw API.
  3. Never copy GitHub's sample hash `39fa2ee980eb94b0:1` into real output. The worked example below uses it purely as a schema placeholder.
- **`guid`** (§3.27.3): a unique, stable per-result GUID. Producers "MAY but do not need to set" it. A result-management system SHOULD assign it on ingest. Two results with the same fingerprint still get distinct guids. The schema enforces a UUID v1-5 pattern (L2094). It is not an identity key across runs, and GitHub does not list it.
- **`correlationGuid`** (§3.27.4, schema L2100): an equivalence-class id for logically identical results. Optional.
- **`baselineState`** (§3.27.24): `new` | `unchanged` | `updated` | `absent` (schema enum L2193; e.g. `fixed` is rejected). `absent` means the result was in the baseline run but not in the current one. So a "fixed" finding is emitted as a result with `baselineState: "absent"`. `run.baselineGuid` (§3.14.5) names the baseline run. Deciding "same result" is left to fingerprints (§3.27.24 NOTE 1). GitHub's SARIF page never mentions `baselineState` (grep of sarif-support.md: no hits), and GitHub does its own new/fixed tracking via `primaryLocationLineHash`. So `baselineState` is useful for local reports and harmless on upload.

### 3. Confidence, severity, suppression, redaction

- **Property bags** (§3.8.1): every SARIF object MAY carry `properties`, holding arbitrary JSON values. Names are hierarchical strings and SHOULD be camelCase. `properties.tags` is a unique string array (schema `propertyBag` L1650). This is where custom confidence goes, e.g. `result.properties = {"confidence": "high", "aama/confidenceScore": 0.9}`. GitHub does not list result-level `properties`, so it ignores them (sarif-support.md:118, 170-180).
- **`rank`** (§3.27.25): a number from 0.0 to 100.0 giving priority/importance. -1.0 means unset. Only meaningful when `kind` = `fail`. Rank values are not comparable across tools. Schema L2204 enforces [-1, 100]. The rule-level default is `defaultConfiguration.rank` (§3.50.4). GitHub does not list `rank`.
- **GitHub severity/confidence knobs are rule-level** (`reportingDescriptor.properties`):
  - `precision` ∈ `very-high|high|medium|low`, meaning how often the rule's results are true. This is GitHub's closest analogue to confidence (sarif-support.md:162).
  - `problem.severity` ∈ `error|warning|recommendation`, for non-security rules (sarif-support.md:163).
  - `security-severity`: a **string** score in (0.0, 10.0]. Setting it makes the rule's results security results. Buckets: >9.0 critical, 7.0-8.9 high, 4.0-6.9 medium, 0.1-3.9 low (sarif-support.md:164).
  - `tags` are used for filtering (sarif-support.md:161).
  - The schema does not type-check `security-severity`, so a numeric 9.8 still passes (verified below). Emit a string.
- **Suppression** (§3.27.23, §3.35):
  - `result.suppressions` is an array of `suppression` objects, each needing `kind` ∈ `inSource|external` (§3.35.2; schema L2713/L2759).
  - Optional `status` ∈ `accepted|underReview|rejected` (§3.35.3), plus `justification` (§3.35.6).
  - An empty array means "not suppressed". Absent or null means "no suppression info".
  - Within one run, results must be all-null or all-non-null (§3.27.23).
  - GitHub does **not** list `suppressions` as a supported property, so a suppressed result is still uploaded as an open alert. Dismissal needs the separate `advanced-security/dismiss-alerts` action, which PATCHes matching alerts to `dismissed` / "Suppressed via SARIF" (dismiss-alerts README L3, L12).
  - The simplest approach for a small tool is to drop suppressed findings from the upload, or keep them only in the local log.
- **Redaction**:
  - SARIF has no per-result "redacted" flag. Redaction applies only to properties the spec marks *redactable*: `invocation.commandLine`, `machine`, `account`, `environmentVariables`, and `versionControlDetails.revisionId`/`branch`/`revisionTag` (§3.20.2, §3.20.15, §3.20.16, §3.20.20, §3.23.4-3.23.6).
  - Redacted text is replaced by a token from `run.redactionTokens`, SHOULD be `"[REDACTED]"` (§3.5.2, §3.14.28).
  - `message.text` is not redactable. A per-finding "redacted" marker is therefore a property-bag key, e.g. `properties["aama/redacted"]: true`.

### 4. Which schema file to vendor, its licence, and validator compatibility

- **Vendor the normative OASIS file**: `https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json`. Spec §3.13.3 NOTE 2 names this exact URL.
  - It declares `"$schema": "http://json-schema.org/draft-04/schema#"` with an `id` of the same URL (schema L2-4).
  - sha256 `c3b4bb2d6093897483348925aaa73af03b3e3f4bd4ca38cef26dcb4212a2682e`. Pin that hash in the test.
- **Licence**:
  - The OASIS Notices (spec front matter, "Copyright © OASIS Open 2023. All Rights Reserved") allow copying and redistribution "in whole or in part, without restriction of any kind, provided that the above copyright notice and this section are included". The document itself "may not be modified".
  - The TC works under the **RF on RAND Terms Mode** of the OASIS IPR Policy (spec Status section; `oasis-tcs/sarif-spec` LICENSE.md). GitHub reports the licence as `NOASSERTION`/"Other".
  - In practice: vendor the file unmodified with a sibling `NOTICE` that carries the OASIS copyright notice.
  - The alternative is the SchemaStore copy (`https://json.schemastore.org/sarif-2.1.0.json`, Draft-07, repo Apache-2.0). It is **not** equivalent: it lacks the `region` `anyOf` (`startLine`/`charOffset`/`byteOffset`), so an empty `region {}` passes there but fails OASIS (verified below).
- **What GitHub actually validates against**:
  - `upload-sarif` validates non-CodeQL SARIF with the npm `jsonschema` package against its vendored `src/sarif-schema-2.1.0.json` (upload-lib.ts L453-518). The `$schema` value in your file is irrelevant to that check.
  - It downgrades `uri`/`uri-reference` format errors to warnings (L476-491, codeql-action issue #1703).
  - That vendored copy declares Draft 2020-12 (L2). Its region `anyOf` sits *inside* `properties` (L1782-1786), so it acts as a property definition and is not enforced. It also fails Python `jsonschema`'s `check_schema` (verified). Passing the OASIS schema is therefore strictly stronger than the action's check.
- **Python `jsonschema`**:
  - Supports Draft 3, 4, 6, 7, 2019-09 and 2020-12. `validator_for` picks the class from `$schema` (python-jsonschema docs).
  - On the OASIS file it selects **`Draft4Validator`**, and `check_schema` passes (verified, jsonschema 4.25.1).
  - Format checking is off unless you pass `format_checker=`.
  - The Draft-4 checker does not know `uri-reference` (its format set is `date-time, email, hostname, idn-email, ipv4, ipv6, regex, uri`), so `artifactLocation.uri` is never format-checked under the OASIS schema. `uri` needs `rfc3987` or `rfc3986-validator` installed.
  - The test's only dependency is `jsonschema` (dev-only). The emitter itself stays stdlib `json`.

### 5. Worked example (1 rule, 1 result): verified

Command (scratch dir `/tmp/claude-1000/sarif-scratch/ex/`, schema fetched as above):

```
uv run --no-project --with jsonschema python validate.py sarif-schema-2.1.0.json floor.sarif gh-min.sarif full.sarif
```

`validate.py` core:

```python
schema = json.load(open(path))
Cls = jsonschema.validators.validator_for(schema); Cls.check_schema(schema)
errors = list(Cls(schema, format_checker=Cls.FORMAT_CHECKER).iter_errors(doc))
```

Outcome, exit 0:
- `jsonschema 4.25.1 validator Draft4Validator`.
- `floor.sarif VALID`, `gh-min.sarif VALID`, `full.sarif VALID`.
- 15 negative mutations of `gh-min` were all INVALID with the expected message: no `message`, `message: {}`, `level: "info"`, `version: "2.1"`, no `driver.name`, `startLine: 0`, `region: {}`, `baselineState: "fixed"`, `guid: "abc"`, non-string fingerprint value, `rank: 101`, suppression without `kind`, top-level `result.confidence`, `ruleIndex: -2`, `physicalLocation: {}`.
- Accepted by the schema but wrong by prose or by GitHub: a result without `ruleId` (§3.27.5 needs it), a URI with a space (format not checked under Draft-4), and a numeric `security-severity`. The emitter's own unit tests must catch these three.

Other schema copies:
- SchemaStore Draft-07: same three accepted, plus `region: {}`.
- codeql-action's copy: `check_schema` raises `SchemaError` on the misplaced `anyOf`. Without `check_schema`, all three examples are VALID under `Draft202012Validator`.

`full.sarif`, the recommended shape: GitHub-complete plus identity, confidence and suppression. Paths and hashes are placeholders.

```json
{
  "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "aa-ma-assess",
          "semanticVersion": "0.1.0",
          "informationUri": "https://github.com/snewhouse/aa-ma-forge",
          "rules": [
            {
              "id": "AAMA001",
              "name": "HighCyclomaticComplexity",
              "shortDescription": {"text": "Function exceeds the complexity threshold."},
              "fullDescription": {"text": "A function's cyclomatic complexity exceeds the configured threshold."},
              "help": {"text": "Split the function into smaller units.", "markdown": "Split the function into smaller units."},
              "defaultConfiguration": {"level": "warning", "rank": 50.0},
              "properties": {"tags": ["maintainability"], "precision": "high", "problem.severity": "warning"}
            }
          ]
        }
      },
      "originalUriBaseIds": {"%SRCROOT%": {"uri": "file:///home/user/repo/"}},
      "results": [
        {
          "ruleId": "AAMA001",
          "ruleIndex": 0,
          "kind": "fail",
          "level": "warning",
          "rank": 72.5,
          "message": {"text": "Function 'parse' has cyclomatic complexity 23 (threshold 15)."},
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {"uri": "src/aa_ma/parser.py", "uriBaseId": "%SRCROOT%"},
                "region": {"startLine": 42, "startColumn": 1, "endLine": 42, "endColumn": 10}
              }
            }
          ],
          "guid": "3f2b8c1e-5d4a-4b6f-9e7d-2a1c0b9f8e7d",
          "fingerprints": {"aamaFinding/v1": "sha256:0f3c9a7e1b2d4c5f"},
          "partialFingerprints": {"primaryLocationLineHash": "39fa2ee980eb94b0:1"},
          "baselineState": "new",
          "suppressions": [
            {"kind": "external", "status": "underReview", "justification": "Known hotspot; refactor ticket open."}
          ],
          "properties": {"confidence": "high", "aama/confidenceScore": 0.9, "aama/redacted": false, "tags": ["complexity"]}
        }
      ]
    }
  ]
}
```

`gh-min.sarif` is the same document minus these fields: `informationUri`, `help.markdown`, `defaultConfiguration.rank`, rule `properties`, `originalUriBaseIds`, `kind`, `rank`, `guid`, `fingerprints`, `baselineState`, `suppressions` and result `properties`. It is the smallest shape that meets every GitHub "Required" row. For a real upload, drop the placeholder `primaryLocationLineHash` and let `upload-sarif` compute it. Also drop `suppressions` unless you intend to run dismiss-alerts. Emission is `json.dumps(log, indent=2)`, no library needed.

## Not pursued
- Porting `fingerprints.ts`'s rolling hash to Python and cross-checking outputs against the action. That is only needed for raw-API uploads.
- Live upload to a GitHub repo (`upload-sarif` or `POST /repos/{o}/{r}/code-scanning/sarifs` with gzip+base64). I did not verify acceptance end to end; the evidence is the docs plus the action's validator source.
- The Microsoft SARIF validator / `Sarif.Multitool validate` GitHub-ingestion ruleset (https://sarifweb.azurewebsites.net/), which GitHub recommends (sarif-support.md:101). It is not run here and may flag rules the schema does not.
- `runAutomationDetails.id` / upload `category`, needed when several SARIF files for one tool and commit are uploaded (sarif-support.md:206-210; upload-lib.ts:1008 `validateUniqueCategory`).
- Whether GitHub's backend (as opposed to the action) re-validates, and against which schema copy. Not documented.
- SARIF 2.2 drafts in `oasis-tcs/sarif-spec`. Out of scope, since the question pins 2.1.0.
- The full Appendix B fingerprint guidance and the `rule`/`reportingDescriptorReference` alternative to `ruleIndex` (§3.27.7, §3.52). Neither is needed for a single-driver tool.
