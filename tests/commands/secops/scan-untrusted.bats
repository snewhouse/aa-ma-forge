#!/usr/bin/env bats
# scan-untrusted.sh: each case plants a finding behind one way a scanned repo can hide it,
# and asserts the script still reports it. The bypasses were reproduced in sdm review of
# fix/secops-untrusted-config (PRs #77/#78, TODOS "secops: a tested scan script").
# Needs git, ruff, shellcheck and gitleaks on PATH; osv-scanner is stubbed.

SCRIPT="${BATS_TEST_DIRNAME}/../../../claude-code/skills/secops/scripts/scan-untrusted.sh"

setup() {
    REPO="${BATS_TEST_TMPDIR}/repo"
    git init -q -b main "${REPO}"
    git -C "${REPO}" config user.email t@t
    git -C "${REPO}" config user.name t
    echo base > "${REPO}/README"
    commit "base"
    git -C "${REPO}" switch -q -c pr
    # why: built at run time so this file never holds a literal the repo's own gitleaks flags
    KEY="AKIA$(printf 'Z%.0s' 1 2 3 4)QWERTYUIOPAS"
}

commit() { git -C "${REPO}" add -A -f . && git -C "${REPO}" commit -q -m "$1"; }
put() { mkdir -p "$(dirname "${REPO}/$1")" && printf '%b' "$2" > "${REPO}/$1"; }
scan() { run "${SCRIPT}" --base main "${REPO}"; }

S602='import subprocess\nsubprocess.run(input(), shell=True)\n'
BASH_UNQUOTED='#!/bin/bash\necho $1\n'

@test "usage error without a repo or base" {
    run "${SCRIPT}"
    [ "${status}" -eq 2 ]
    run "${SCRIPT}" "${REPO}"
    [ "${status}" -eq 2 ]
}

@test "an unknown ref is a usage error, not a clean scan" {
    run "${SCRIPT}" --base no-such-ref "${REPO}"
    [ "${status}" -eq 2 ]
}

@test "a clean change exits 0 with no findings" {
    put ok.py 'print("hi")\n'
    commit "ok"
    scan
    [ "${status}" -eq 0 ]
    [[ "${lines[-1]}" == "scan-untrusted: findings=0 suppressors=0 unknown=0" ]]
}

@test "ruff: S602 behind noqa, per-file-ignores and a gitignored path is reported" {
    put a.py "${S602%\\n}  # noqa: S602\n"
    put pyproject.toml '[tool.ruff.lint.per-file-ignores]\n"*" = ["S"]\n'
    put hidden/b.py "${S602}"
    put .gitignore 'hidden/\n'
    commit "pr"
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"FINDING ruff a.py:2"*"S602"* ]]
    [[ "${output}" == *"FINDING ruff hidden/b.py:2"*"S602"* ]]
}

@test "ruff: a file named like an option does not silence the scan" {
    put a.py "${S602}"
    # A python-shebang file is selected for Ruff, so its name lands on the command line.
    put '--ignore=S602' '#!/usr/bin/env python3\nprint(1)\n'
    commit "pr"
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"FINDING ruff a.py:2"*"S602"* ]]
}

@test "ruff: an extensionless python script is scanned" {
    put bin/tool "#!/usr/bin/env python3\n${S602}"
    commit "pr"
    scan
    [[ "${output}" == *"FINDING ruff bin/tool:3"*"S602"* ]]
}

@test "shellcheck: .shellcheckrc disable=all and no .sh extension do not hide a finding" {
    put .shellcheckrc 'disable=all\n'
    put bin/deploy "${BASH_UNQUOTED}"
    put '--severity=error' '#!/bin/sh\ntrue\n'   # SC2086 is info: this name would hide it
    commit "pr"
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"FINDING shellcheck bin/deploy:2"*"SC2086"* ]]
    [[ "${output}" == *"SUPPRESSOR .shellcheckrc scanner config changed"* ]]
}

@test "inline suppressions added in the range are reported" {
    put a.sh '#!/bin/sh\n# shellcheck disable=SC2086\necho $1\n'
    put b.py 'x = 1  # noqa: S105\n'
    commit "pr"
    scan
    [[ "${output}" == *"SUPPRESSOR a.sh:2 shellcheck directive"* ]]
    [[ "${output}" == *"SUPPRESSOR b.py:1 noqa"* ]]
}

@test "gitleaks: the repo's .gitleaksignore and .gitleaks.toml do not hide a secret" {
    put creds.txt "aws=${KEY}\n"
    commit "pr"
    # The repo lists the leak's own fingerprints, then allowlists every path as well.
    gitleaks detect --no-banner -s "${REPO}" --report-format json \
        --report-path "${BATS_TEST_TMPDIR}/r.json" --exit-code 0 2>/dev/null
    jq -r '.[].Fingerprint' "${BATS_TEST_TMPDIR}/r.json" > "${REPO}/.gitleaksignore"
    [ -s "${REPO}/.gitleaksignore" ]
    put .gitleaks.toml '[allowlist]\npaths = [".*"]\n'
    commit "ignore"
    run gitleaks detect --no-banner -s "${REPO}" --exit-code 1
    [ "${status}" -eq 0 ]   # precondition: gitleaks alone is fooled
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"FINDING gitleaks creds.txt"*"aws-access-token"* ]]
    [[ "${output}" != *"${KEY}"* ]]
}

@test "gitleaks: a .gitleaksignore in the working directory does not apply" {
    put creds.txt "aws=${KEY}\n"
    commit "pr"
    cd "${REPO}"
    gitleaks detect --no-banner --no-git -s . --report-format json --report-path "${BATS_TEST_TMPDIR}/r.json" --exit-code 0 2>/dev/null
    jq -r '.[].Fingerprint' "${BATS_TEST_TMPDIR}/r.json" > .gitleaksignore
    scan
    [[ "${output}" == *"FINDING gitleaks creds.txt"* ]]
}

@test "gitleaks: a secret added then deleted inside the range is reported" {
    put old.txt "aws=${KEY}\n"
    commit "add"
    git -C "${REPO}" rm -q old.txt
    commit "delete"
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"FINDING gitleaks old.txt"* ]]
}

@test "gitleaks: paths in the default allowlist are scanned" {
    put vendor/x.bin "aws=${KEY}\n"
    put package-lock.json "{\"k\": \"${KEY}\"}\n"
    commit "pr"
    scan
    [[ "${output}" == *"FINDING gitleaks vendor/x.bin"* ]]
    [[ "${output}" == *"FINDING gitleaks package-lock.json"* ]]
}

@test "gitleaks: .gitattributes -diff does not blind the scan" {
    put .gitattributes '* -diff\n'
    put creds.cfg "aws=${KEY}\n"
    put b.py 'x = 1  # noqa: S105\n'
    commit "pr"
    scan
    [[ "${output}" == *"FINDING gitleaks creds.cfg"* ]]
    [[ "${output}" == *"SUPPRESSOR b.py:1 noqa"* ]]
    [[ "${output}" == *"SUPPRESSOR .gitattributes scanner config changed"* ]]
}

@test "gitleaks: an inline gitleaks:allow is reported as a suppressor" {
    put creds.txt "aws=${KEY} # gitleaks:allow\n"
    commit "pr"
    scan
    [[ "${output}" == *"SUPPRESSOR creds.txt:1 gitleaks:allow"* ]]
}

@test "a secret already on the base is out of scope" {
    git -C "${REPO}" switch -q main
    put creds.txt "aws=${KEY}\n"
    commit "on main"
    git -C "${REPO}" switch -q pr
    git -C "${REPO}" merge -q main -m merge
    put ok.py 'print("hi")\n'
    commit "pr"
    scan
    [ "${status}" -eq 0 ]
    [[ "${output}" != *"FINDING gitleaks"* ]]
}

@test "osv-scanner: run with the operator's --config, never the repo's osv-scanner.toml" {
    stub="${BATS_TEST_TMPDIR}/osv-scanner"
    printf '#!/bin/sh\necho "$@" > "%s/osv.args"\necho %s\nexit 1\n' "${BATS_TEST_TMPDIR}" \
        "'{\"results\":[{\"packages\":[{\"vulnerabilities\":[{\"id\":\"GHSA-test\"}]}]}]}'" > "${stub}"
    chmod +x "${stub}"
    put web/package-lock.json '{}\n'
    put web/osv-scanner.toml '[[IgnoredVulns]]\nid = "GHSA-test"\n'
    commit "pr"
    OSV_SCANNER_BIN="${stub}" scan
    [[ "${output}" == *"FINDING osv-scanner web/package-lock.json GHSA-test"* ]]
    [[ "${output}" == *"SUPPRESSOR web/osv-scanner.toml scanner config changed"* ]]
    args=$(cat "${BATS_TEST_TMPDIR}/osv.args")
    [[ "${args}" == *"--config"* && "${args}" != *"web/osv-scanner.toml"* ]]
}

@test "a scanner that cannot run is UNKNOWN (exit 3), never a clean zero" {
    put a.py 'print("hi")\n'
    put web/package-lock.json '{}\n'
    commit "pr"
    RUFF_BIN=/nonexistent OSV_SCANNER_BIN=/nonexistent scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN ruff"* ]]
    [[ "${output}" == *"UNKNOWN osv-scanner"* ]]
}

@test "a changed Python lockfile points to pip-audit as UNKNOWN" {
    put uv.lock 'version = 1\n'
    commit "pr"
    scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN pip-audit uv.lock"* ]]
}

@test "ruff: assert (S101) is reported in source, not in test files" {
    put a.py 'assert input()\n'
    put tests/test_a.py 'assert 1\n'
    put conftest.py 'assert 1\n'
    commit "pr"
    scan
    [[ "${output}" == *"FINDING ruff a.py:1 S101"* ]]
    [[ "${output}" != *"tests/test_a.py:1 S101"* && "${output}" != *"conftest.py:1 S101"* ]]
}

@test "suppression markers count only in files a scanner reads them from" {
    put notes.md 'Use `# noqa: S602` and `# shellcheck disable=SC2086` sparingly.\n'
    put creds.txt "aws=${KEY} # gitleaks:allow\n"
    commit "pr"
    scan
    [[ "${output}" != *"SUPPRESSOR notes.md"* ]]
    [[ "${output}" == *"SUPPRESSOR creds.txt:1 gitleaks:allow"* ]]
}

@test "gitleaks:allow in an earlier commit's version of a file is reported" {
    put creds.txt "aws=${KEY} # gitleaks:allow\n"
    commit "add allowed"
    put creds.txt "nothing here\n"
    commit "edit"
    scan
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"SUPPRESSOR creds.txt:1 gitleaks:allow"* ]]
}

@test "an added line that looks like a diff header cannot re-target marker detection" {
    put a.py 'x = 1\n++ b/notes.md\ny = "s"  # noqa: S105\n'
    commit "pr"
    scan
    [[ "${output}" == *"SUPPRESSOR a.py:3 noqa"* ]]
}

@test "shellcheck: a disable directive already on the base does not hide new code" {
    git -C "${REPO}" switch -q main
    put a.sh '#!/bin/bash\n# shellcheck disable=SC2086\ntrue\n'
    commit "base directive"
    git -C "${REPO}" switch -q pr
    git -C "${REPO}" merge -q main -m merge
    put a.sh '#!/bin/bash\n# shellcheck disable=SC2086\ntrue\necho $1\n'
    commit "pr"
    scan
    [[ "${output}" == *"FINDING shellcheck a.sh:4 SC2086"* ]]
    [[ "${output}" == *"SUPPRESSOR a.sh:2 shellcheck directive"* ]]
}

@test "shellcheck: a multi-key directive (source=… disable=…) is reported and blanked" {
    put a.sh '#!/bin/bash\n# shellcheck source=/dev/null disable=SC2086\necho $1\n'
    put b.sh '#!/bin/bash\n#shellcheck enable=all disable=SC2086\necho $1\n'
    commit "pr"
    scan
    [[ "${output}" == *"FINDING shellcheck a.sh:3 SC2086"* ]]
    [[ "${output}" == *"FINDING shellcheck b.sh:3 SC2086"* ]]
    [[ "${output}" == *"SUPPRESSOR a.sh:2 shellcheck directive"* ]]
    [[ "${output}" == *"SUPPRESSOR b.sh:2 shellcheck directive"* ]]
}

@test "shellcheck: an invalid byte after a directive does not stop it being blanked" {
    put a.sh '#!/bin/bash\n# shellcheck disable=SC2086 \xff\necho $1\n'
    commit "pr"
    LC_ALL=C.UTF-8 scan
    [[ "${output}" == *"FINDING shellcheck a.sh:3 SC2086"* ]]
}

@test "a file name with a control character is UNKNOWN, never a silent clean" {
    printf '#!/usr/bin/env python3\n%b' "${S602}" > "${REPO}/run"$'\n'
    commit "pr"
    scan
    [ "${status}" -ne 0 ]
    [[ "${output}" == *"UNKNOWN path with control characters"* ]]
}

@test "ruff: a file it cannot decode is UNKNOWN" {
    put lat.py '# -*- coding: latin-1 -*-\nx = "\xe9"\nimport subprocess\nsubprocess.run(input(), shell=True)\n'
    commit "pr"
    scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN ruff could not lint lat.py"* ]]
}

@test "ruff: a file it cannot parse is UNKNOWN" {
    put s.py "${S602}x = (\n"
    commit "pr"
    scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN ruff could not parse s.py"* ]]
}

@test "ruff: a uv run --script shebang is scanned" {
    put tool "#!/usr/bin/env -S uv run --script\n${S602}"
    commit "pr"
    scan
    [[ "${output}" == *"FINDING ruff tool:3"*"S602"* ]]
}

@test "symlinks are scanned by their own name with their target's content" {
    put data/blob "${S602}"
    put data/steps "${BASH_UNQUOTED}"
    mkdir -p "${REPO}/pkg"
    ln -s ../data/blob "${REPO}/pkg/mod.py"
    ln -s data/steps "${REPO}/setup.sh"
    commit "pr"
    scan
    [[ "${output}" == *"FINDING ruff pkg/mod.py:2"*"S602"* ]]
    [[ "${output}" == *"FINDING shellcheck setup.sh:2"*"SC2086"* ]]
}

@test "a symlink pointing outside the repo is UNKNOWN" {
    ln -s /etc/passwd "${REPO}/x.py"
    commit "pr"
    scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN symlink x.py"* ]]
}

@test "scripts no scanner reads (other interpreters, notebooks, .pth) are UNKNOWN" {
    put bin/run '#!/usr/bin/env node\nrequire("child_process").exec(process.argv[2])\n'
    put nb.ipynb '{}\n'
    put hook.pth 'import os\n'
    commit "pr"
    scan
    [ "${status}" -eq 3 ]
    [[ "${output}" == *"UNKNOWN not scanned bin/run"* ]]
    [[ "${output}" == *"UNKNOWN not scanned nb.ipynb"* ]]
    [[ "${output}" == *"UNKNOWN not scanned hook.pth"* ]]
}

@test "a git error while reading the range exits 2, not clean" {
    put sub/a.txt 'x\n'
    commit "pr"
    tree=$(git -C "${REPO}" rev-parse HEAD:sub)
    rm -f "${REPO}/.git/objects/${tree:0:2}/${tree:2}"
    scan
    [ "${status}" -eq 2 ]
}

@test "shellcheck: bats files are scanned" {
    put t.bats '#!/usr/bin/env bats\n@test "x" {\n    echo $1\n}\n'
    commit "pr"
    scan
    [[ "${output}" == *"FINDING shellcheck t.bats:3 SC2086"* ]]
}
