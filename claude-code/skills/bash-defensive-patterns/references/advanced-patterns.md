<!-- Derived from https://github.com/wshobson/agents/plugins/shell-scripting/skills/bash-defensive-patterns/SKILL.md @ 5d65aa1 on 2026-10-09 — aa-ma-forge v0.17.0 -->
## Advanced Defensive Techniques

### Named Parameters Pattern

```bash
#!/bin/bash
set -Eeuo pipefail

process_data() {
    local input_file=""
    local output_dir=""
    local format="json"

    # Parse named parameters
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --input=*)
                input_file="${1#*=}"
                ;;
            --output=*)
                output_dir="${1#*=}"
                ;;
            --format=*)
                format="${1#*=}"
                ;;
            *)
                echo "ERROR: Unknown parameter: $1" >&2
                return 1
                ;;
        esac
        shift
    done

    # Validate required parameters
    [[ -n "$input_file" ]] || { echo "ERROR: --input is required" >&2; return 1; }
    [[ -n "$output_dir" ]] || { echo "ERROR: --output is required" >&2; return 1; }
}
```

### Dependency Checking

```bash
#!/bin/bash
set -Eeuo pipefail

check_dependencies() {
    local -a missing_deps=()
    local -a required=("jq" "curl" "git")

    for cmd in "${required[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo "ERROR: Missing required commands: ${missing_deps[*]}" >&2
        return 1
    fi
}

check_dependencies
```

## Best Practices Summary

1. **Always use strict mode** - `set -Eeuo pipefail`
2. **Quote all variables** - `"$variable"` prevents word splitting
3. **Use [[ ]] conditionals** - More robust than [ ]
4. **Implement error trapping** - Catch and handle errors gracefully
5. **Validate all inputs** - Check file existence, permissions, formats
6. **Use functions for reusability** - Prefix with meaningful names
7. **Implement structured logging** - Include timestamps and levels
8. **Support dry-run mode** - Allow users to preview changes
9. **Handle temporary files safely** - Use mktemp, cleanup with trap
10. **Design for idempotency** - Scripts should be safe to rerun
11. **Document requirements** - List dependencies and minimum versions
12. **Test error paths** - Ensure error handling works correctly
13. **Use `command -v`** - Safer than `which` for checking executables
14. **Prefer printf over echo** - More predictable across systems

## Resources

- **Bash Strict Mode**: http://redsymbol.net/articles/unofficial-bash-strict-mode/
- **Google Shell Style Guide**: https://google.github.io/styleguide/shellguide.html
- **Defensive BASH Programming**: https://www.lifepipe.net/
