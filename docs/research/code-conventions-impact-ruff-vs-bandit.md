# Ruff S vs Bandit — does Ruff cover every Bandit test that fires here?

- Question: can `ruff check --select S` replace the Bandit CI job (code-conventions-impact M8.1, plan D12 / A4)?
- Versions (venv-pinned, M1.2): **ruff 0.15.9**, **bandit 1.9.4**. Measured 2026-10-12 on `feat/cci-m8-secops-ci-baseline` @ 0df379c.
- Scope scanned: `src packages scripts` (the paths CI will gate). `tests/` is out of scope; see §Scope.

## Commands

```bash
uv run bandit -q -r src packages scripts -f json -o bandit.json          # rc 1, 39 results
uv run ruff check --isolated --select S --output-format json src packages scripts            # 36
uv run ruff check --isolated --select S --preview --output-format json src packages scripts  # 51
uv run bandit --help        # "The following tests were discovered and loaded" → 75 IDs
uv run ruff rule --all --output-format json   # linter == flake8-bandit → 73 S rules
```

## What fired on this repo

| Bandit ID | Name | Severity | Bandit hits | Ruff code | Ruff hits | Ruff status at 0.15.9 |
|-----------|------|----------|------------:|-----------|----------:|-----------------------|
| B101 | assert_used | LOW | 1 | S101 | 1 | stable |
| B404 | import_subprocess | LOW | 11 | S404 | 15 (preview only) | **preview** |
| B603 | subprocess_without_shell_equals_true | LOW | 15 | S603 | 20 | stable |
| B607 | start_process_with_partial_path | LOW | 9 | S607 | 11 | stable |
| B608 | hardcoded_sql_expressions | MEDIUM | 3 | S608 | 4 | stable |
| **Total** | | | **39** | | **36 stable / 51 preview** | |

Per-site cross-check (script compared `(file, line, code)` triples):

- **Every Bandit hit has a Ruff hit on the same call.** 11 sat on a different line only because the two
  tools anchor multi-line calls differently: Bandit marks `subprocess.run(` for B607, Ruff marks the argv
  line (`["git", …]`); on two calls the offset was −1 or −2 lines. There was no hit for Bandit alone.
- **Ruff reports more because it ignores `# nosec`.** It flagged 8 sites Bandit had suppressed
  (`codemem/draw/views.py:204-205`, `codemem/indexer.py:410`, `aa_ma/analysis/{run.py:191, secrets.py:406,
  stamp.py:162-163}`, `aa_ma/render/mermaid_lint.py:518`). Each gets a `# noqa: S60x  # why:` in M8.2,
  carrying over its existing `nosec` rationale.
- **B404 / S404** fires on every `import subprocess`. Ruff has it as preview only. It is informational:
  every real subprocess call is already reported by S603/S607 at the call site.

## Every Bandit 1.9.4 test → Ruff 0.15.9

The numbering follows flake8-bandit (`Bnnn` → `Snnn`). Each row was checked by name against `ruff rule --all`.

| Bandit | Name | Ruff | Ruff name | Status |
|--------|------|------|-----------|--------|
| B101 | assert_used | S101 | assert | stable |
| B102 | exec_used | S102 | exec-builtin | stable |
| B103 | set_bad_file_permissions | S103 | bad-file-permissions | stable |
| B104 | hardcoded_bind_all_interfaces | S104 | hardcoded-bind-all-interfaces | stable |
| B105 | hardcoded_password_string | S105 | hardcoded-password-string | stable |
| B106 | hardcoded_password_funcarg | S106 | hardcoded-password-func-arg | stable |
| B107 | hardcoded_password_default | S107 | hardcoded-password-default | stable |
| B108 | hardcoded_tmp_directory | S108 | hardcoded-temp-file | stable |
| B110 | try_except_pass | S110 | try-except-pass | stable |
| B112 | try_except_continue | S112 | try-except-continue | stable |
| B113 | request_without_timeout | S113 | request-without-timeout | stable |
| B201 | flask_debug_true | S201 | flask-debug-true | stable |
| B202 | tarfile_unsafe_members | S202 | tarfile-unsafe-members | stable |
| B301 | pickle | S301 | suspicious-pickle-usage | stable |
| B302 | marshal | S302 | suspicious-marshal-usage | stable |
| B303 | md5 | S303 | suspicious-insecure-hash-usage | stable |
| B304 | ciphers | S304 | suspicious-insecure-cipher-usage | stable |
| B305 | cipher_modes | S305 | suspicious-insecure-cipher-mode-usage | stable |
| B306 | mktemp_q | S306 | suspicious-mktemp-usage | stable |
| B307 | eval | S307 | suspicious-eval-usage | stable |
| B308 | mark_safe | S308 | suspicious-mark-safe-usage | stable |
| B310 | urllib_urlopen | S310 | suspicious-url-open-usage | stable |
| B311 | random | S311 | suspicious-non-cryptographic-random-usage | stable |
| B312 | telnetlib | S312 | suspicious-telnet-usage | stable |
| B313 | xml_bad_cElementTree | S313 | suspicious-xmlc-element-tree-usage | stable |
| B314 | xml_bad_ElementTree | S314 | suspicious-xml-element-tree-usage | stable |
| B315 | xml_bad_expatreader | S315 | suspicious-xml-expat-reader-usage | stable |
| B316 | xml_bad_expatbuilder | S316 | suspicious-xml-expat-builder-usage | stable |
| B317 | xml_bad_sax | S317 | suspicious-xml-sax-usage | stable |
| B318 | xml_bad_minidom | S318 | suspicious-xml-mini-dom-usage | stable |
| B319 | xml_bad_pulldom | S319 | suspicious-xml-pull-dom-usage | stable |
| B321 | ftplib | S321 | suspicious-ftp-lib-usage | stable |
| B323 | unverified_context | S323 | suspicious-unverified-context-usage | stable |
| B324 | hashlib_insecure_functions | S324 | hashlib-insecure-hash-function | stable |
| B401 | import_telnetlib | S401 | suspicious-telnetlib-import | preview |
| B402 | import_ftplib | S402 | suspicious-ftplib-import | preview |
| B403 | import_pickle | S403 | suspicious-pickle-import | preview |
| B404 | import_subprocess | S404 | suspicious-subprocess-import | preview |
| B405 | import_xml_etree | S405 | suspicious-xml-etree-import | preview |
| B406 | import_xml_sax | S406 | suspicious-xml-sax-import | preview |
| B407 | import_xml_expat | S407 | suspicious-xml-expat-import | preview |
| B408 | import_xml_minidom | S408 | suspicious-xml-minidom-import | preview |
| B409 | import_xml_pulldom | S409 | suspicious-xml-pulldom-import | preview |
| B411 | import_xmlrpclib | S411 | suspicious-xmlrpc-import | preview |
| B412 | import_httpoxy | S412 | suspicious-httpoxy-import | preview |
| B413 | import_pycrypto | S413 | suspicious-pycrypto-import | preview |
| B415 | import_pyghmi | S415 | suspicious-pyghmi-import | preview |
| B501 | request_with_no_cert_validation | S501 | request-with-no-cert-validation | stable |
| B502 | ssl_with_bad_version | S502 | ssl-insecure-version | stable |
| B503 | ssl_with_bad_defaults | S503 | ssl-with-bad-defaults | stable |
| B504 | ssl_with_no_version | S504 | ssl-with-no-version | stable |
| B505 | weak_cryptographic_key | S505 | weak-cryptographic-key | stable |
| B506 | yaml_load | S506 | unsafe-yaml-load | stable |
| B507 | ssh_no_host_key_verification | S507 | ssh-no-host-key-verification | stable |
| B508 | snmp_insecure_version | S508 | snmp-insecure-version | stable |
| B509 | snmp_weak_cryptography | S509 | snmp-weak-cryptography | stable |
| B601 | paramiko_calls | S601 | paramiko-call | stable |
| B602 | subprocess_popen_with_shell_equals_true | S602 | subprocess-popen-with-shell-equals-true | stable |
| B603 | subprocess_without_shell_equals_true | S603 | subprocess-without-shell-equals-true | stable |
| B604 | any_other_function_with_shell_equals_true | S604 | call-with-shell-equals-true | stable |
| B605 | start_process_with_a_shell | S605 | start-process-with-a-shell | stable |
| B606 | start_process_with_no_shell | S606 | start-process-with-no-shell | stable |
| B607 | start_process_with_partial_path | S607 | start-process-with-partial-path | stable |
| B608 | hardcoded_sql_expressions | S608 | hardcoded-sql-expression | stable |
| B609 | linux_commands_wildcard_injection | S609 | unix-command-wildcard-injection | stable |
| B610 | django_extra_used | S610 | django-extra | stable |
| B611 | django_rawsql_used | S611 | django-raw-sql | stable |
| B612 | logging_config_insecure_listen | S612 | logging-config-insecure-listen | stable |
| B613 | trojansource | **GAP** (in S) | — | covered outside S by `PLE2502` bidirectional-unicode (stable; 0 hits in src/packages/scripts/tests) |
| B614 | pytorch_load | **GAP** | — | no `torch` import in this repo |
| B615 | huggingface_unsafe_download | **GAP** | — | no `huggingface_hub` / `transformers` import |
| B701 | jinja2_autoescape_false | S701 | jinja2-autoescape-false | stable |
| B702 | use_of_mako_templates | S702 | mako-templates | stable |
| B703 | django_mark_safe | **GAP** | — | its call (`mark_safe`) is S308; no `django` import |
| B704 | markupsafe_markup_xss | S704 | unsafe-markup-use | stable |

Totals: 75 Bandit tests; 71 map to a Ruff S rule (58 stable, 13 preview: S401–S415). There are 4 GAPs,
and none can fire on this codebase today.

## B404 decision input (A4)

- Bandit B404 fires 11× here (the plan's 2026-10-08 baseline said 10×; one `import subprocess` has been
  added since). Ruff `S404` is **preview-only** at 0.15.9, so a stable `--select S` never reports it.
- What it flags is an import, not a call. 10 of the 11 importing modules call subprocess, and every call
  is already reported by S603/S607 (stable). The 11th, `codemem/cli.py:27`, imports it only to catch
  `subprocess.CalledProcessError`, so it has no call to report at all. A gate on B404 adds a finding per
  importing module and catches nothing S603/S607 does not. (Ruff's preview S404 shows 15 because it also
  reports the 4 `# nosec` files Bandit suppresses.)
- **Recommendation: ruff-only.** The fallback ID list would contain nothing that can fire: B404 is
  redundant with S603/S607, and B613/B614/B615/B703 cannot fire on this codebase. Revisit if `torch`,
  `huggingface_hub` or `django` enters the dependency tree (B614/B615/B703 would then be GAPs that matter),
  or if Ruff stabilises S404.

## Scope

`tests/` is excluded from the CI gate. Bandit in tests reported 122 hits (M7 Stage C, disputed: S101 asserts
and fixture subprocess calls). The plan keeps only the `tests/**` S101 per-file ignore (M8.2).

## §deps — vulnerable package triage

Method: pip-audit 2.10.1 over `uv export --frozen --no-emit-workspace --no-emit-project` (hashed, `--strict`)
on 2026-10-12. Baseline: **72 findings in 13 packages** (46 unique advisory IDs; pip-audit lists some twice). CI `deps` run 38276289265 matched it.
A blanket `uv lock --upgrade-package` of all 13 was rejected: it moved `mcp` to 2.3.0 (a major) and *downgraded*
fastmcp. Upgrades were therefore made within existing constraints, plus `mcp>=1.29.1,<2` in the dev group.

| Package | Was | Now | Unique advisories | Resolution |
|---------|-----|-----|-----------:|------------|
| anyio | 4.13.0 | 4.14.2 | 2 | upgraded |
| authlib | 1.6.10 | 1.8.0 | 2 | upgraded |
| cryptography | 46.0.7 | 50.0.2 | 4 | upgraded (transitive, via pyjwt/authlib) |
| idna | 3.11 | 3.20 | 1 | upgraded |
| mcp | 1.27.0 | 1.30.0 | 3 | upgraded, held `<2`; live stdio round-trip with the codemem server OK (15 tools) |
| pydantic-settings | 2.13.1 | 2.15.0 | 1 | upgraded |
| pyjwt | 2.12.1 | 2.15.1 | 15 | upgraded (no-fix PYSEC-2026-4146 no longer reported) |
| pytest | 9.0.2 | 9.1.1 | 1 | upgraded (dev) |
| python-multipart | 0.0.26 | 0.0.32 | 4 | upgraded |
| starlette | 1.0.0 | 1.7.0 | 5 | upgraded |
| urllib3 | 2.6.3 | 2.8.0 | 5 | upgraded |
| fastmcp | 2.14.7 | 2.14.7 | 2 | **ignored to 2027-01-12**: PYSEC-2026-2475 (Gemini-CLI install; never used) and PYSEC-2026-2476 (OAuth proxy; the server is stdio-only). The fix needs fastmcp ≥3.2, which needs `watchfiles>=1` while aa-ma pins `<1` (TUI). TODOS P2 |
| diskcache | 5.6.3 | 5.6.3 | 1 | **ignored to 2027-01-12**: PYSEC-2026-2447 has no fixed release; pulled in by fastmcp's py-key-value-aio, which codemem never configures |

After triage: 0 unignored advisories. Ignores live in `.pip-audit-ignore` (ID, expiry, why), and
`tests/security/test_deps_audit.py` fails any expired entry. Decision approved by Ste (M8.5).
