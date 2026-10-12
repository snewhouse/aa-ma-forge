#!/usr/bin/env bash
# Deploy the export service.
set -euo pipefail
rsync -a ./ deploy@host:/srv/app/
