#!/usr/bin/env bash
# Copies the canonical Bob package (bob-package/) into samples/carddemo/,
# which is the folder you actually open as the Bob IDE workspace root.
# bob-package/ stays the single source of truth for version control and
# for judges reviewing the repo; this script is how it reaches the place
# Bob actually reads from.
#
# Run this again any time you edit files under bob-package/.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=bob-package
DEST=samples/carddemo

if [ ! -d "$SRC/.bob" ]; then
  echo "error: $SRC/.bob not found -- run this from the blast-radius repo root" >&2
  exit 1
fi

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$SRC/.bob/" "$DEST/.bob/"
else
  rm -rf "$DEST/.bob"
  cp -r "$SRC/.bob" "$DEST/.bob"
fi

cp "$SRC/carddemo.bobignore" "$DEST/.bobignore"

echo "pushed $SRC/.bob -> $DEST/.bob"
echo "pushed $SRC/carddemo.bobignore -> $DEST/.bobignore"
echo
echo "Open '$DEST' as the Bob IDE workspace root. Do NOT open the parent"
echo "blast-radius/ folder -- that would put docs/ground_truth/ inside"
echo "Bob's visible tree (the outer .bobignore covers that case too, but"
echo "the isolated workspace is the real protection)."
