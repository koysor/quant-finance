#!/usr/bin/env bash
# Build the library docs with Zensical, failing on any warning.
#
# `zensical build --strict` aborts on broken links and similar problems, but
# it only prints griffe's docstring warnings (an undocumented parameter, a
# missing annotation), which `mkdocs build --strict` used to treat as errors.
# This script restores that by failing when any griffe warning appears.
#
# Usage: scripts/build_docs.sh          (from the repo root; output in site/)
set -euo pipefail
cd "$(dirname "$0")/.."

log=$(mktemp)
trap 'rm -f "$log"' EXIT

status=0
uv run --locked --group docs zensical build --strict --clean 2>&1 | tee "$log" || status=$?
if [ "$status" -ne 0 ]; then
  echo "build_docs: zensical build failed (exit $status)" >&2
  exit "$status"
fi
if grep -q '^griffe:' "$log"; then
  echo "build_docs: griffe reported docstring warnings (see above); fix them" >&2
  exit 1
fi
