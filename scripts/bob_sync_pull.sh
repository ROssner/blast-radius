#!/usr/bin/env bash
# Copies Bob's run output (reports + intermediate artifacts) out of the
# isolated samples/carddemo/ workspace and back into the main repo, so
# reports/ and bob-package/ reflect the latest run for anyone browsing the
# repo without opening Bob themselves.
#
# Run this after a pipeline run completes in Bob.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=samples/carddemo/.blast-radius
mkdir -p reports bob-package/run-artifacts

if [ ! -d "$SRC" ]; then
  echo "error: $SRC not found -- has a pipeline run happened yet?" >&2
  exit 1
fi

if [ -d "$SRC/reports" ]; then
  cp -v "$SRC"/reports/*.html reports/ 2>/dev/null || echo "no report HTML files found yet"
fi

if [ -d "$SRC/artifacts" ]; then
  cp -rv "$SRC/artifacts" bob-package/run-artifacts/latest
fi

echo
echo "pulled reports -> reports/"
echo "pulled artifacts -> bob-package/run-artifacts/latest/"
