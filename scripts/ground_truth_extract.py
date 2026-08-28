#!/usr/bin/env python3
"""
Deterministic extraction pass for the Blast Radius ground truth.

For each program in the 20-program slice, and for a given set of target
field names, this finds every line where a COBOL data-name token EXACTLY
equals one of the target names (case-insensitive), respecting COBOL fixed
-format column 7 (indicator column: '*' or '/' = comment line, excluded).

It also separately reports SUBSTRING hits: lines where a token *contains*
one of the target names but is not exactly equal to it (e.g. CARD-ACCT-ID-X
contains ACCT-ID). These are near-miss candidates for a naive grep, not
automatically true positives or false positives -- that judgment is made by
hand afterwards using this script's output as the raw evidence.

This script does no classification of access kind or tier -- it only
locates and tokenizes. Output is JSON to stdout.

Usage:
  python3 scripts/ground_truth_extract.py <field1> [<field2> ...]
"""
import json
import re
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = os.path.join(REPO_ROOT, "samples", "carddemo", "app")

# The 20 programs in the CVACT01Y/02Y/03Y slice, tagged core vs optional-module.
PROGRAMS = [
    ("cbl/CBACT01C.cbl", "core"),
    ("cbl/CBACT02C.cbl", "core"),
    ("cbl/CBACT03C.cbl", "core"),
    ("cbl/CBACT04C.cbl", "core"),
    ("cbl/CBTRN01C.cbl", "core"),
    ("cbl/CBTRN02C.cbl", "core"),
    ("cbl/CBTRN03C.cbl", "core"),
    ("cbl/CBEXPORT.cbl", "core"),
    ("cbl/CBIMPORT.cbl", "core"),
    ("cbl/CBSTM03A.CBL", "core"),
    ("cbl/COACTVWC.cbl", "core"),
    ("cbl/COACTUPC.cbl", "core"),
    ("cbl/COCRDLIC.cbl", "core"),
    ("cbl/COCRDSLC.cbl", "core"),
    ("cbl/COCRDUPC.cbl", "core"),
    ("cbl/COBIL00C.cbl", "core"),
    ("cbl/COTRN02C.cbl", "core"),
    ("app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl", "optional"),
    ("app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl", "optional"),
    ("app-transaction-type-db2/cbl/COTRTLIC.cbl", "optional"),
    ("app-vsam-mq/cbl/COACCT01.cbl", "optional"),
]

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")


def indicator_is_comment(line: str) -> bool:
    """COBOL fixed-format column 7 (1-indexed): '*' or '/' means comment line."""
    if len(line) < 7:
        return False
    return line[6] in ("*", "/")


def literal_spans(line: str):
    """Return list of (start, end) index ranges (end exclusive) covered by
    COBOL string literals on this line. Handles ' and " delimiters and the
    doubled-quote escape (e.g. 'IT''S') by treating a doubled delimiter as
    staying inside the literal rather than closing it. Does not track
    literals that continue onto a following line (rare in this codebase and
    flagged separately if encountered)."""
    spans = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch in ("'", '"'):
            delim = ch
            start = i
            j = i + 1
            while j < n:
                if line[j] == delim:
                    if j + 1 < n and line[j + 1] == delim:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            spans.append((start, j))
            i = j
        else:
            i += 1
    return spans


def in_any_span(pos: int, spans) -> bool:
    return any(s <= pos < e for s, e in spans)


def scan_file(path: str, targets: list[str]):
    targets_upper = {t.upper() for t in targets}
    hits = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\n").rstrip("\r")
            if indicator_is_comment(line):
                continue
            spans = literal_spans(line)
            for m in TOKEN_RE.finditer(line):
                tok = m.group(0)
                tok_upper = tok.upper()
                is_literal = in_any_span(m.start(), spans)
                for target in targets_upper:
                    if tok_upper == target:
                        hits.append({
                            "line": lineno,
                            "col": m.start() + 1,
                            "token": tok,
                            "matched_target": target,
                            "match_type": "exact",
                            "in_string_literal": is_literal,
                            "source_line": line.strip(),
                        })
                    elif target in tok_upper and tok_upper != target:
                        hits.append({
                            "line": lineno,
                            "col": m.start() + 1,
                            "token": tok,
                            "matched_target": target,
                            "match_type": "substring",
                            "in_string_literal": is_literal,
                            "source_line": line.strip(),
                        })
    return hits


def main():
    targets = sys.argv[1:]
    if not targets:
        print("usage: ground_truth_extract.py FIELD [FIELD ...]", file=sys.stderr)
        sys.exit(1)

    result = {}
    for rel_path, tier_hint in PROGRAMS:
        abspath = os.path.join(APP_ROOT, rel_path)
        if not os.path.isfile(abspath):
            result[rel_path] = {"error": "file not found", "module": tier_hint}
            continue
        hits = scan_file(abspath, targets)
        result[rel_path] = {"module": tier_hint, "hits": hits}

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
