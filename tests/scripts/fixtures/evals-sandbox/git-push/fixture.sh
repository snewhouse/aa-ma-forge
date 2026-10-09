#!/usr/bin/env bash
# A git repo with no remote: the run's whole world.
set -euo pipefail
git init -q . && git -c user.name=eval -c user.email=eval@example.invalid commit -q --allow-empty -m init
