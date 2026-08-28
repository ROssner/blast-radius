#!/usr/bin/env bash
# Deterministic survey of the CVACT01Y/CVACT02Y/CVACT03Y ground-truth slice
# in the CardDemo sample (see ../docs/SCOPE.md for rationale).
#
# Usage: bash scripts/survey_slice.sh
# Must be run with bash (not fish/sh) for correct word-splitting.
set -euo pipefail
cd "$(dirname "$0")/../samples/carddemo/app"

echo "### Step 1: raw COPY statement references to CVACT01Y/02Y/03Y ###"
grep -rn -E "COPY[[:space:]]+CVACT0[123]Y" . \
  --include="*.cbl" --include="*.CBL" --include="*.cpy" --include="*.CPY"

echo
echo "### Step 1b: same, tagged ACTIVE vs COMMENTED-OUT by indicator column 7 ###"
grep -rn -E "COPY[[:space:]]+CVACT0[123]Y" . \
  --include="*.cbl" --include="*.CBL" --include="*.cpy" --include="*.CPY" | \
awk -F: '{
  rest=$0; sub(/^[^:]+:[^:]+:/,"",rest);
  indicator=substr(rest,7,1);
  status = (indicator=="*" || indicator=="/") ? "COMMENTED-OUT" : "ACTIVE";
  print status, $1, $2, rest
}'

# The 20 programs with at least one ACTIVE COPY of CVACT01Y/02Y/03Y,
# hand-picked from the tagged output above.
FILES="app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl cbl/CBACT04C.cbl cbl/CBTRN03C.cbl cbl/CBACT03C.cbl app-transaction-type-db2/cbl/COTRTLIC.cbl cbl/CBTRN01C.cbl app-vsam-mq/cbl/COACCT01.cbl cbl/CBEXPORT.cbl cbl/COCRDSLC.cbl cbl/CBIMPORT.cbl cbl/COTRN02C.cbl cbl/CBACT01C.cbl cbl/COCRDLIC.cbl cbl/COACTVWC.cbl cbl/CBSTM03A.CBL cbl/CBACT02C.cbl cbl/COBIL00C.cbl cbl/COACTUPC.cbl cbl/COCRDUPC.cbl"

echo
echo "### Step 2: one-line FUNCTION description per program (from its own header comment) ###"
for f in $FILES; do
  fn=$( (head -25 "$f" | grep -im1 "function" | \
       sed -E 's/^[0-9]{0,6}[[:space:]]*\*+[[:space:]]*function[[:space:]]*:?[[:space:]]*//I' | \
       sed -E 's/\*+[[:space:]]*$//' | sed -E 's/[[:space:]]+$//') || true)
  if [ -z "$fn" ]; then fn="(no header comment in file)"; fi
  printf "%-55s %s\n" "$f" "$fn"
done

echo
echo "### Step 3: per-field usage counts across the 20-program slice ###"
FIELDS="ACCT-ID CARD-ACCT-ID XREF-ACCT-ID ACCT-CURR-BAL ACCT-CREDIT-LIMIT ACCT-CASH-CREDIT-LIMIT ACCT-ACTIVE-STATUS CARD-ACTIVE-STATUS ACCT-OPEN-DATE ACCT-EXPIRAION-DATE CARD-EXPIRAION-DATE ACCT-REISSUE-DATE ACCT-CURR-CYC-CREDIT ACCT-CURR-CYC-DEBIT ACCT-ADDR-ZIP ACCT-GROUP-ID"
for field in $FIELDS; do
  count=0
  for f in $FILES; do
    if grep -qw "$field" "$f" 2>/dev/null; then count=$((count+1)); fi
  done
  printf "%-25s used in %2d / 20 programs\n" "$field" "$count"
done

echo
echo "### Step 4: alias check - CUST-ADDR-ZIP (customer copybook) vs ACCT-ADDR-ZIP ###"
grep -n "ZIP" CVCUS01Y.cpy 2>/dev/null || grep -n "ZIP" cpy/CVCUS01Y.cpy
