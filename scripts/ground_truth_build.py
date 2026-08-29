#!/usr/bin/env python3
"""
Assembles the final ground-truth JSON files in docs/ground_truth/ from:
  1. ground_truth_extract.py's deterministic line-level extraction (source
     of truth for every line number and source line's exact text), and
  2. hand-verified classification data below (tier, access kind, and notes),
     which were derived by reading the actual files -- see docs/SCOPE.md and
     the conversation record for the verification trail (e.g. checking each
     zero-exact-hit program's READ/WRITE statements to confirm group-level
     vs field-level access, and checking whether a COPY is entirely dead).

Re-run with: python3 scripts/ground_truth_build.py
Regenerates docs/ground_truth/ACCT-ID.json and docs/ground_truth/ACCT-ADDR-ZIP.json.
"""
import json
import os
import re
import collections
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "docs", "ground_truth")
EXTRACT = os.path.join(REPO_ROOT, "scripts", "ground_truth_extract.py")


def run_extract(*targets):
    out = subprocess.run([sys.executable, EXTRACT, *targets],
                          capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def module_of(path, data):
    return data[path]["module"]


# ---------------------------------------------------------------------------
# FIELD 1: ACCT-ID (wide) -- aliases ACCT-ID / CARD-ACCT-ID / XREF-ACCT-ID
# ---------------------------------------------------------------------------

WIDE_TARGETS = ["ACCT-ID", "CARD-ACCT-ID", "XREF-ACCT-ID"]

# Hand-verified access-kind + note for every true (non-literal, exact) hit.
# Key: (program path, line number, matched target) -> (access_kind, note)
WIDE_HIT_NOTES = {
    ("cbl/CBACT01C.cbl", 201, "ACCT-ID"): ("DISPLAY",
        "the leading 'ACCT-ID :' text on this line is a report-label string literal, not a field reference -- the trailing bare ACCT-ID token is the real DISPLAY operand"),
    ("cbl/CBACT01C.cbl", 216, "ACCT-ID"): ("MOVE-SOURCE", "copied into OUT-ACCT-ID, a sequential-file output record field"),
    ("cbl/CBACT01C.cbl", 254, "ACCT-ID"): ("MOVE-SOURCE", "copied into ARR-ACCT-ID, an array/report output record field"),
    ("cbl/CBACT01C.cbl", 277, "ACCT-ID"): ("MOVE-SOURCE", "copied into VB1-ACCT-ID, a variable-block output record field"),

    ("cbl/CBACT04C.cbl", 486, "ACCT-ID"): ("MOVE-SOURCE",
        "concatenated via STRING into TRAN-DESC (an interest-transaction description) -- data flow is out of ACCT-ID same as a MOVE source"),

    ("cbl/CBTRN01C.cbl", 175, "XREF-ACCT-ID"): ("MOVE-SOURCE", "bridges the XREF-ACCT-ID and ACCT-ID aliases directly: confirms both names denote the same logical value"),
    ("cbl/CBTRN01C.cbl", 175, "ACCT-ID"): ("MOVE-TARGET", "receives the value carried by XREF-ACCT-ID on the same line"),
    ("cbl/CBTRN01C.cbl", 178, "ACCT-ID"): ("DISPLAY", "error message: 'ACCOUNT <id> NOT FOUND'"),
    ("cbl/CBTRN01C.cbl", 237, "XREF-ACCT-ID"): ("DISPLAY",
        "DISPLAY 'ACCOUNT ID : ' XREF-ACCT-ID -- the human-facing label 'ACCOUNT ID' is mapped directly onto the XREF-ACCT-ID code name, the concrete alias evidence for this field"),
    ("cbl/CBTRN01C.cbl", 242, "ACCT-ID"): ("MOVE-SOURCE", "copied into FD-ACCT-ID, a file-record field"),

    ("cbl/CBTRN02C.cbl", 394, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into FD-ACCT-ID, a file-record field"),
    ("cbl/CBTRN02C.cbl", 469, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into FD-TRANCAT-ACCT-ID, a transaction-category file-record field"),
    ("cbl/CBTRN02C.cbl", 505, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into TRANCAT-ACCT-ID"),

    ("cbl/CBTRN03C.cbl", 364, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into TRAN-REPORT-ACCOUNT-ID, a print-report line field"),

    ("cbl/CBEXPORT.cbl", 44, "ACCT-ID"): ("READ",
        "RECORD KEY IS ACCT-ID in FILE-CONTROL: ACCT-ID is the VSAM record key for ACCTFILE-FILE, so every keyed read/write against this file is keyed on this exact field"),
    ("cbl/CBEXPORT.cbl", 351, "ACCT-ID"): ("MOVE-SOURCE", "copied into EXP-ACCT-ID, the branch-migration export record (CVEXPORT.cpy) -- this is how the value crosses into CBIMPORT.cbl via the export file"),
    ("cbl/CBEXPORT.cbl", 417, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into EXP-XREF-ACCT-ID (export record)"),
    ("cbl/CBEXPORT.cbl", 536, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into EXP-CARD-ACCT-ID (export record)"),

    ("cbl/CBIMPORT.cbl", 328, "ACCT-ID"): ("MOVE-TARGET", "received from EXP-ACCT-ID -- reverse of CBEXPORT.cbl:351"),
    ("cbl/CBIMPORT.cbl", 359, "XREF-ACCT-ID"): ("MOVE-TARGET", "received from EXP-XREF-ACCT-ID"),
    ("cbl/CBIMPORT.cbl", 408, "CARD-ACCT-ID"): ("MOVE-TARGET", "received from EXP-CARD-ACCT-ID"),

    ("cbl/CBSTM03A.CBL", 396, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-M03B-KEY, used as a statement-lookup key"),
    ("cbl/CBSTM03A.CBL", 398, "XREF-ACCT-ID"): ("READ", "referenced via LENGTH OF (its byte length, not its value) to size WS-M03B-KEY-LN"),
    ("cbl/CBSTM03A.CBL", 483, "ACCT-ID"): ("MOVE-SOURCE", "copied into ST-ACCT-ID (statement print line)"),
    ("cbl/CBSTM03A.CBL", 529, "ACCT-ID"): ("MOVE-SOURCE", "copied into L11-ACCT (statement print line)"),

    ("cbl/COACTUPC.cbl", 3805, "ACCT-ID"): ("MOVE-SOURCE",
        "copied into CDEMO-ACCT-ID, a field of CARDDEMO-COMMAREA (COCOM01Y.cpy); this program XCTLs onward with COMMAREA(CARDDEMO-COMMAREA) at line 956, so this value is passed to another program"),
    ("cbl/COACTUPC.cbl", 3817, "ACCT-ID"): ("MOVE-SOURCE", "copied into ACUP-OLD-ACCT-ID, a before-image working field used later to detect whether the account id changed"),

    ("cbl/COCRDLIC.cbl", 1167, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-ROW-ACCTNO(WS-SCRN-COUNTER), a screen-row display table entry (statement spans lines 1167-1168)"),
    ("cbl/COCRDLIC.cbl", 1174, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CA-FIRST-CARD-ACCT-ID, tracks the first card shown on this screen page (statement spans lines 1174-1175)"),
    ("cbl/COCRDLIC.cbl", 1194, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CA-LAST-CARD-ACCT-ID, tracks the last card shown on this screen page"),
    ("cbl/COCRDLIC.cbl", 1212, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CA-LAST-CARD-ACCT-ID (statement spans lines 1212-1213)"),
    ("cbl/COCRDLIC.cbl", 1236, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CA-LAST-CARD-ACCT-ID"),
    ("cbl/COCRDLIC.cbl", 1340, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-ROW-ACCTNO(WS-SCRN-COUNTER) (statement spans lines 1340-1341)"),
    ("cbl/COCRDLIC.cbl", 1350, "CARD-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CA-FIRST-CARD-ACCT-ID (statement spans lines 1350-1351)"),
    ("cbl/COCRDLIC.cbl", 1386, "CARD-ACCT-ID"): ("COMPARE", "IF CARD-ACCT-ID = CC-ACCT-ID -- compared against the commarea's filter value"),

    ("cbl/COBIL00C.cbl", 170, "ACCT-ID"): ("MOVE-TARGET", "receives screen input ACTIDINI OF COBIL0AI (statement spans lines 170-171, moves to two targets)"),
    ("cbl/COBIL00C.cbl", 171, "XREF-ACCT-ID"): ("MOVE-TARGET", "second receiving field of the same MOVE started at line 170"),
    ("cbl/COBIL00C.cbl", 349, "ACCT-ID"): ("READ", "RIDFLD(ACCT-ID) -- used as the VSAM record-key field for a CICS keyed READ"),
    ("cbl/COBIL00C.cbl", 350, "ACCT-ID"): ("READ", "KEYLENGTH(LENGTH OF ACCT-ID) -- supports the keyed read above"),
    ("cbl/COBIL00C.cbl", 414, "XREF-ACCT-ID"): ("READ", "RIDFLD(XREF-ACCT-ID) -- keyed CICS READ of the cross-reference file"),
    ("cbl/COBIL00C.cbl", 415, "XREF-ACCT-ID"): ("READ", "KEYLENGTH(LENGTH OF XREF-ACCT-ID)"),

    ("cbl/COTRN02C.cbl", 206, "XREF-ACCT-ID"): ("MOVE-TARGET", "receives WS-ACCT-ID-N (a numeric-edited copy of screen input)"),
    ("cbl/COTRN02C.cbl", 223, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied out to the screen field ACTIDINI OF COTRN2AI"),
    ("cbl/COTRN02C.cbl", 582, "XREF-ACCT-ID"): ("READ", "RIDFLD(XREF-ACCT-ID) -- keyed CICS READ"),
    ("cbl/COTRN02C.cbl", 583, "XREF-ACCT-ID"): ("READ", "KEYLENGTH(LENGTH OF XREF-ACCT-ID)"),

    ("app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl", 868, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CARD-RID-ACCT-ID, a VSAM alternate-index key work field"),

    ("app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl", 523, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into WS-CARD-RID-ACCT-ID"),
    ("app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl", 619, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into PA-ACCT-ID (authorization-decision working record)"),
    ("app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl", 805, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into PA-ACCT-ID"),
    ("app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl", 911, "XREF-ACCT-ID"): ("MOVE-SOURCE", "copied into PA-ACCT-ID"),

    ("app-vsam-mq/cbl/COACCT01.cbl", 408, "ACCT-ID"): ("MOVE-SOURCE", "copied into WS-ACCT-ID, staged for the MQ reply message"),
}

# Programs with zero true exact hits: verified structural evidence
# (group-level READ/WRITE/DISPLAY/MOVE of the whole record, never the field
# by name) for each alias whose copybook is actively COPY'd there.
WIDE_STRUCTURAL = {
    "cbl/CBACT02C.cbl": [
        {"alias": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD",
         "evidence": [
             {"line": 78, "source_line": "DISPLAY CARD-RECORD"},
             {"line": 93, "source_line": "READ CARDFILE-FILE INTO CARD-RECORD."},
         ]},
    ],
    "cbl/CBACT03C.cbl": [
        {"alias": "XREF-ACCT-ID", "copybook": "CVACT03Y", "record": "CARD-XREF-RECORD",
         "evidence": [
             {"line": 78, "source_line": "DISPLAY CARD-XREF-RECORD"},
             {"line": 93, "source_line": "READ XREFFILE-FILE INTO CARD-XREF-RECORD."},
         ]},
    ],
    "cbl/COACTVWC.cbl": [
        {"alias": "ACCT-ID", "copybook": "CVACT01Y", "record": "ACCOUNT-RECORD",
         "evidence": [
             {"line": 780, "source_line": "INTO      (ACCOUNT-RECORD)"},
             {"line": 781, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"},
         ]},
        {"alias": "XREF-ACCT-ID", "copybook": "CVACT03Y", "record": "CARD-XREF-RECORD",
         "evidence": [
             {"line": 731, "source_line": "INTO      (CARD-XREF-RECORD)"},
             {"line": 732, "source_line": "LENGTH    (LENGTH OF CARD-XREF-RECORD)"},
         ]},
        {"alias": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD",
         "dead_copy": True,
         "evidence": [],
         "note": "COPY CVACT02Y is active (line 248) but CARD-RECORD is never referenced anywhere else in this file -- not read, not written, not displayed. This alias is effectively unaffected in this program despite the COPY being present."},
    ],
    "cbl/COCRDSLC.cbl": [
        {"alias": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD",
         "evidence": [
             {"line": 746, "source_line": "INTO      (CARD-RECORD)"},
             {"line": 747, "source_line": "LENGTH    (LENGTH OF CARD-RECORD)"},
             {"line": 787, "source_line": "INTO      (CARD-RECORD)"},
             {"line": 788, "source_line": "LENGTH    (LENGTH OF CARD-RECORD)"},
         ],
         "note": "This program declares CARD-ACCT-ID-X/CARD-ACCT-ID-N (CICS-OUTPUT-EDIT-VARS, lines 73-74) and WS-CARD-RID-ACCT-ID (lines 99-101), which look like aliases but are NOT populated from the copybook's CARD-ACCT-ID field -- CARD-ACCT-ID-X/-N are declared but never referenced again anywhere in the file (dead fields), and WS-CARD-RID-ACCT-ID's only assignment (line 739, 'MOVE CC-ACCT-ID-N TO WS-CARD-RID-ACCT-ID') is commented out (indicator column 7 = '*'). Verified via `grep -n WS-CARD-RID-ACCT-ID` plus manual column-7 check."},
    ],
    "cbl/COCRDUPC.cbl": [
        {"alias": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD",
         "evidence": [
             {"line": 1386, "source_line": "INTO      (CARD-RECORD)"},
             {"line": 1387, "source_line": "LENGTH    (LENGTH OF CARD-RECORD)"},
             {"line": 1432, "source_line": "INTO      (CARD-RECORD)"},
             {"line": 1433, "source_line": "LENGTH    (LENGTH OF CARD-RECORD)"},
         ]},
    ],
}

# Programs whose relationship to the field is a pure DEAD COPY: the
# copybook is actively COPY'd, but the corresponding record is never
# touched anywhere else in the file -- not by field name, not even at
# group level (no READ/WRITE/DISPLAY/MOVE of the whole record either).
# This is its own tier, not a variant of STRUCTURALLY-AFFECTED, because
# STRUCTURALLY-AFFECTED requires real group-level I/O as evidence.
WIDE_DEAD_COPY = {
    "app-transaction-type-db2/cbl/COTRTLIC.cbl": [
        {"alias": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD",
         "copy_line": 490,
         "note": (
             "Active `COPY CVACT02Y.` at line 490, but CARD-RECORD never appears "
             "anywhere else in the file (grep for CARD-RECORD returns nothing), and "
             "there are zero exact or substring hits for any of the three "
             "account-id aliases anywhere in this program. Unlike COCRDSLC/COCRDUPC/"
             "COACTVWC there is no group-level I/O either -- the COPY is entirely "
             "vestigial. A field-width change to CARD-ACCT-ID has zero effect on "
             "this program's behavior."
         )},
    ],
}

# Per-alias dead-copy footnotes on programs that are otherwise tiered via a
# DIFFERENT alias/copybook (so the program's overall tier is unaffected).
WIDE_DEAD_COPY_FOOTNOTES = {
    "cbl/COTRN02C.cbl": [
        {"alias": "ACCT-ID", "copybook": "CVACT01Y", "record": "ACCOUNT-RECORD",
         "copy_line": 89,
         "note": (
             "Active `COPY CVACT01Y.` at line 89, but ACCOUNT-RECORD never appears "
             "anywhere else in the file, and none of the 12 ACCT-* fields declared "
             "in CVACT01Y (ACCT-ID, ACCT-ACTIVE-STATUS, ACCT-CURR-BAL, "
             "ACCT-CREDIT-LIMIT, ACCT-CASH-CREDIT-LIMIT, ACCT-OPEN-DATE, "
             "ACCT-EXPIRAION-DATE, ACCT-REISSUE-DATE, ACCT-CURR-CYC-CREDIT, "
             "ACCT-CURR-CYC-DEBIT, ACCT-ADDR-ZIP, ACCT-GROUP-ID) is referenced "
             "anywhere in the file. This program's overall tier for the wide field "
             "stays FIELD-AWARE (it genuinely uses XREF-ACCT-ID from CVACT03Y) -- "
             "this footnote covers the ACCT-ID/CVACT01Y relationship specifically, "
             "which is a dead copy."
         )},
    ],
}

WIDE_UNCERTAIN = []


def build_wide():
    data = run_extract(*WIDE_TARGETS)
    programs_out = []
    field_aware_paths = set()

    for path, pdata in data.items():
        exact_hits = [h for h in pdata["hits"]
                      if h["match_type"] == "exact" and not h["in_string_literal"]]
        if exact_hits:
            field_aware_paths.add(path)
            hit_entries = []
            for h in exact_hits:
                key = (path, h["line"], h["matched_target"])
                if key not in WIDE_HIT_NOTES:
                    raise SystemExit(f"UNCLASSIFIED HIT (fix WIDE_HIT_NOTES): {key} -> {h['source_line']}")
                access_kind, note = WIDE_HIT_NOTES[key]
                hit_entries.append({
                    "alias": h["matched_target"],
                    "line": h["line"],
                    "access_kind": access_kind,
                    "source_line": h["source_line"],
                    "note": note,
                })
            hit_entries.sort(key=lambda x: x["line"])
            programs_out.append({
                "path": path,
                "module": pdata["module"],
                "tier": "FIELD-AWARE",
                "hits": hit_entries,
                "also_structural": WIDE_STRUCTURAL.get(path, []),
                "dead_copy_footnotes": WIDE_DEAD_COPY_FOOTNOTES.get(path, []),
            })

    for path, entries in WIDE_STRUCTURAL.items():
        if path in field_aware_paths:
            continue
        programs_out.append({
            "path": path,
            "module": data[path]["module"],
            "tier": "STRUCTURALLY-AFFECTED",
            "hits": [],
            "structural_evidence": entries,
        })

    for path, entries in WIDE_DEAD_COPY.items():
        if path in field_aware_paths or path in WIDE_STRUCTURAL:
            continue
        programs_out.append({
            "path": path,
            "module": data[path]["module"],
            "tier": "DEAD-COPY",
            "hits": [],
            "dead_copy_evidence": entries,
        })

    # near misses: distinct locally-derived identifiers, not the true aliases.
    # Dedup on (token, path, line): a single physical line can match more than
    # one of the three search targets as a substring of the same identifier
    # (e.g. CARD-ACCT-ID-X contains both ACCT-ID and CARD-ACCT-ID), which
    # otherwise double-counts that line for the same identifier.
    true_targets_upper = {t.upper() for t in WIDE_TARGETS}
    seen_token_path_line = set()
    by_token = collections.defaultdict(list)
    for path, pdata in data.items():
        for h in pdata["hits"]:
            if h["match_type"] != "substring" or h["token"].upper() in true_targets_upper:
                continue
            key = (h["token"].upper(), path, h["line"])
            if key in seen_token_path_line:
                continue
            seen_token_path_line.add(key)
            by_token[h["token"].upper()].append({"path": path, "line": h["line"], "source_line": h["source_line"]})

    near_misses = []
    for tok in sorted(by_token, key=lambda t: -len(by_token[t])):
        locs = by_token[tok]
        by_prog = collections.defaultdict(list)
        for loc in locs:
            by_prog[loc["path"]].append(loc["line"])
        near_misses.append({
            "identifier": tok,
            "total_occurrences": len(locs),
            "programs": [{"path": p, "lines": sorted(ls)} for p, ls in sorted(by_prog.items())],
        })

    programs_out.sort(key=lambda p: (p["module"], p["path"]))

    result = {
        "field": "ACCT-ID (wide)",
        "aliases": {
            "ACCT-ID": {"copybook": "CVACT01Y", "record": "ACCOUNT-RECORD", "pic": "9(11)"},
            "CARD-ACCT-ID": {"copybook": "CVACT02Y", "record": "CARD-RECORD", "pic": "9(11)"},
            "XREF-ACCT-ID": {"copybook": "CVACT03Y", "record": "CARD-XREF-RECORD", "pic": "9(11)"},
        },
        "tier_definitions": {
            "FIELD-AWARE": "names at least one of the three exact field tokens (ACCT-ID / CARD-ACCT-ID / XREF-ACCT-ID) somewhere in its own code, outside of string literals",
            "STRUCTURALLY-AFFECTED": "COPYs a copybook containing one of the aliases and performs whole-group I/O (READ/WRITE/DISPLAY/MOVE) on the record, but never names the field itself",
            "DEAD-COPY": "COPYs a copybook containing one of the aliases, but never touches the resulting record at all -- not by field name, not even at group level. Real technical debt the tool surfaces for free.",
        },
        "methodology": (
            "scripts/ground_truth_extract.py tokenizes each program's non-comment "
            "text (COBOL column 7 checked per line) and flags exact token matches "
            "against the three alias names, excluding matches inside quoted string "
            "literals. Tier and access-kind classification for every hit below was "
            "then verified by hand against the actual source (see notes per hit); "
            "re-run scripts/ground_truth_build.py to regenerate this file from that "
            "classification data plus a fresh extraction pass."
        ),
        "programs": programs_out,
        "near_misses": {
            "summary": (
                f"{sum(nm['total_occurrences'] for nm in near_misses)} lines across "
                f"{len(near_misses)} distinct locally-declared identifiers contain "
                "ACCT-ID, CARD-ACCT-ID, or XREF-ACCT-ID as a substring without being "
                "that exact field -- these are working-storage shadow/edit/commarea "
                "variables (e.g. CDEMO-ACCT-ID, CC-ACCT-ID, WS-CARD-RID-ACCT-ID) that "
                "a naive substring grep for 'ACCT-ID' would wrongly attribute to the "
                "copybook field. None of these are false positives in the sense of "
                "being irrelevant to the real-world account-id value -- most are "
                "genuinely downstream copies of it -- but they are not the field "
                "itself and a precision metric should not credit a tool for finding "
                "them as if it had found ACCT-ID/CARD-ACCT-ID/XREF-ACCT-ID."
            ),
            "distinct_identifiers": near_misses,
        },
        "uncertain": WIDE_UNCERTAIN,
    }
    return result


# ---------------------------------------------------------------------------
# RECLASSIFICATION (2026-08-29): the alias rule
#
# Adopted after reviewing Bob's own SPEC output (spec-acct-id.json), which
# treats commarea/work-area carriers fed by an explicit MOVE as aliases.
# Applied here independently -- verified against source, not copied from
# Bob's claims or the prior near-miss list. See docs/ground_truth/CHANGELOG.md
# for the full rationale. This is a separate, explicit transformation pass
# over build_wide()'s original output, not a rewrite of the original
# extraction/classification logic above.
#
# RULE: a field is an ALIAS of the target if the target's value flows into
# it via an explicit MOVE (in either direction -- both operands of a MOVE
# must co-widen or the narrower one truncates), OR if it REDEFINES a field
# that is itself alias-confirmed (they share the same storage, so one MOVE
# feeds both), OR if it receives the target's value via a whole-record
# READ ... INTO from a record that contains the target field (the 2026-08-29
# extension: a field-width change to the source record requires a matching
# change to every receiving record's corresponding field, or the READ
# misaligns/truncates on that field -- the same risk a literal MOVE poses,
# just via positional record I/O instead of a field-level statement).
#
# A field stays a NEAR MISS only if it is a genuinely different, unrelated
# entity (different real-world data), OR if it is declared but demonstrably
# never fed by anything (dead code -- not a "different entity", just no
# entity at all).
#
# EXCLUDED FROM SCORING: WS-CARD-RID-ACCT-ID and its -X redefine, in the one
# program (COACCT01.cbl) where their only feed is WS-KEY, itself never
# assigned via any MOVE in that file. Plausible but unprovable from this
# file alone. Counted as neither a true positive nor a false positive.
# ---------------------------------------------------------------------------

# identifier -> 'alias' (every occurrence reclassifies) | per-program dict
# mapping program path substring -> 'alias' | 'dead' | 'excluded'
ALIAS_VERDICTS = {
    'CC-ACCT-ID': 'alias', 'CDEMO-ACCT-ID': 'alias', 'WS-ACCT-ID': 'alias',
    'FD-XREF-ACCT-ID': 'alias', 'CC-ACCT-ID-N': 'alias',
    'WS-CA-LAST-CARD-ACCT-ID': 'alias', 'PA-ACCT-ID': 'alias',
    'WS-CA-FIRST-CARD-ACCT-ID': 'alias', 'TRANCAT-ACCT-ID': 'alias',
    'ACUP-NEW-ACCT-ID-X': 'alias', 'EXP-XREF-ACCT-ID': 'alias',
    'EXP-CARD-ACCT-ID': 'alias', 'ACUP-NEW-ACCT-ID': 'alias',
    'FD-TRANCAT-ACCT-ID': 'alias', 'ST-ACCT-ID': 'alias',
    'ACUP-OLD-ACCT-ID-X': 'alias', 'ACUP-OLD-ACCT-ID': 'alias',
    'WS-ACCT-ID-N': 'alias', 'OUT-ACCT-ID': 'alias', 'ARR-ACCT-ID': 'alias',
    'VB1-ACCT-ID': 'alias', 'VB2-ACCT-ID': 'alias', 'EXP-ACCT-ID': 'alias',
    'CARD-UPDATE-ACCT-ID': 'alias',
    # decision 1 (READ INTO extension): all four programs now alias, incl. CBACT01C
    'FD-ACCT-ID': 'alias',
    # decision 3: genuinely dead everywhere they're declared
    'CARD-ACCT-ID-X': 'dead', 'CARD-ACCT-ID-N': 'dead',
    'CUST-ACCT-ID-X': 'dead', 'CUST-ACCT-ID-N': 'dead',
    # decision 2: per-program split, verified against source
    'WS-CARD-RID-ACCT-ID': {
        'COPAUA0C.cbl': 'alias', 'COPAUS0C.cbl': 'alias',
        'COACTUPC.cbl': 'alias', 'COACTVWC.cbl': 'alias',
        'COCRDLIC.cbl': 'dead', 'COCRDSLC.cbl': 'dead', 'COCRDUPC.cbl': 'dead',
        'COACCT01.cbl': 'excluded',
    },
    'WS-CARD-RID-ACCT-ID-X': {
        'COPAUA0C.cbl': 'alias', 'COPAUS0C.cbl': 'alias',
        'COACTUPC.cbl': 'alias', 'COACTVWC.cbl': 'alias',
        'COCRDLIC.cbl': 'dead', 'COCRDSLC.cbl': 'dead', 'COCRDUPC.cbl': 'dead',
        'COACCT01.cbl': 'excluded',
    },
}

# Evidence citation for the newly-confirmed alias identifiers (not per-line --
# see CHANGELOG.md for why access-kind is not hand-classified per line at
# this volume).
ALIAS_EVIDENCE = {
    'CC-ACCT-ID': "CVCRD01Y (COPY, shared) -- app/cbl/COCRDUPC.cbl:752 MOVE CC-ACCT-ID TO CDEMO-ACCT-ID",
    'CDEMO-ACCT-ID': "COCOM01Y (COPY, shared) -- app/cbl/COACTUPC.cbl:3805 MOVE ACCT-ID TO CDEMO-ACCT-ID",
    'WS-ACCT-ID': "local WS, per-program -- app/app-vsam-mq/cbl/COACCT01.cbl:408 MOVE ACCT-ID TO WS-ACCT-ID; app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl:208 MOVE CDEMO-ACCT-ID TO WS-ACCT-ID",
    'FD-XREF-ACCT-ID': "local FD, per-program -- app/cbl/CBACT04C.cbl:204 MOVE TRANCAT-ACCT-ID TO FD-XREF-ACCT-ID",
    'CC-ACCT-ID-N': "CVCRD01Y (COPY, shared), REDEFINES CC-ACCT-ID -- app/cbl/COCRDUPC.cbl:490 MOVE CDEMO-ACCT-ID TO CC-ACCT-ID-N",
    'WS-CA-LAST-CARD-ACCT-ID': "local WS, per-program -- app/cbl/COCRDLIC.cbl:1194 MOVE CARD-ACCT-ID TO WS-CA-LAST-CARD-ACCT-ID",
    'PA-ACCT-ID': "local WS, per-program -- app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:619 MOVE XREF-ACCT-ID TO PA-ACCT-ID",
    'WS-CA-FIRST-CARD-ACCT-ID': "local WS, per-program -- app/cbl/COCRDLIC.cbl:1174-75 MOVE CARD-ACCT-ID TO WS-CA-FIRST-CARD-ACCT-ID",
    'TRANCAT-ACCT-ID': "CVTRA01Y (COPY, shared) -- app/cbl/CBTRN02C.cbl:505 MOVE XREF-ACCT-ID TO TRANCAT-ACCT-ID",
    'ACUP-NEW-ACCT-ID-X': "local WS, per-program, REDEFINES ACUP-NEW-ACCT-ID -- app/cbl/COACTUPC.cbl:759-761",
    'EXP-XREF-ACCT-ID': "CVEXPORT (COPY, shared) -- app/cbl/CBEXPORT.cbl:417 / CBIMPORT.cbl:359",
    'EXP-CARD-ACCT-ID': "CVEXPORT (COPY, shared) -- app/cbl/CBEXPORT.cbl:536 / CBIMPORT.cbl:408",
    'ACUP-NEW-ACCT-ID': "local WS, per-program -- app/cbl/COACTUPC.cbl:1801 MOVE CC-ACCT-ID TO ACUP-NEW-ACCT-ID",
    'FD-TRANCAT-ACCT-ID': "local FD, per-program -- app/cbl/CBTRN02C.cbl:469 MOVE XREF-ACCT-ID TO FD-TRANCAT-ACCT-ID",
    'ST-ACCT-ID': "local WS, per-program -- app/cbl/CBSTM03A.CBL:483 MOVE ACCT-ID TO ST-ACCT-ID",
    'ACUP-OLD-ACCT-ID-X': "local WS, per-program, REDEFINES ACUP-OLD-ACCT-ID -- app/cbl/COACTUPC.cbl:671-673",
    'ACUP-OLD-ACCT-ID': "local WS, per-program -- app/cbl/COACTUPC.cbl:3817 MOVE ACCT-ID TO ACUP-OLD-ACCT-ID",
    'WS-ACCT-ID-N': "local WS, per-program -- app/cbl/COTRN02C.cbl:206 MOVE WS-ACCT-ID-N TO XREF-ACCT-ID",
    'OUT-ACCT-ID': "local WS (output record), per-program -- app/cbl/CBACT01C.cbl:216 MOVE ACCT-ID TO OUT-ACCT-ID",
    'ARR-ACCT-ID': "local WS (output record), per-program -- app/cbl/CBACT01C.cbl:254 MOVE ACCT-ID TO ARR-ACCT-ID",
    'VB1-ACCT-ID': "local WS (output record), per-program -- app/cbl/CBACT01C.cbl:277 MOVE ACCT-ID TO VB1-ACCT-ID VB2-ACCT-ID",
    'VB2-ACCT-ID': "local WS (output record), per-program -- same statement as VB1-ACCT-ID, app/cbl/CBACT01C.cbl:277-278",
    'EXP-ACCT-ID': "CVEXPORT (COPY, shared) -- app/cbl/CBEXPORT.cbl:351 / CBIMPORT.cbl:328",
    'CARD-UPDATE-ACCT-ID': "local WS, per-program -- app/cbl/COCRDUPC.cbl:1463 MOVE CC-ACCT-ID-N TO CARD-UPDATE-ACCT-ID",
    'FD-ACCT-ID': (
        "local FD, per-program -- explicit MOVE in CBTRN01C.cbl:242, CBTRN02C.cbl:394, "
        "CBACT04C.cbl:202; in CBACT01C.cbl fed only via 'READ ACCTFILE-FILE INTO "
        "ACCOUNT-RECORD' (line 166), a whole-record positional copy from a record "
        "containing ACCT-ID -- qualifies under the 2026-08-29 READ INTO extension, not "
        "an explicit field-level MOVE"
    ),
    'WS-CARD-RID-ACCT-ID': (
        "local WS, per-program, split verdict -- alias in COPAUS0C.cbl:868, "
        "COPAUA0C.cbl:523, COACTUPC.cbl:3892, COACTVWC.cbl:691 (all explicit MOVE from "
        "an alias); dead in COCRDLIC/COCRDSLC/COCRDUPC (only candidate bridge is "
        "commented out, column 7 = '*'); excluded from scoring in COACCT01.cbl (fed by "
        "WS-KEY, itself never assigned via any MOVE in that file)"
    ),
    'WS-CARD-RID-ACCT-ID-X': "REDEFINES WS-CARD-RID-ACCT-ID; mirrors its per-program verdict exactly",
}


def classify_access_kind_auto(source_line: str, alias: str) -> str:
    """Lightweight pattern classifier for the newly-reclassified alias hits.
    Not a substitute for the hand classification given to the original 47
    hits -- see CHANGELOG.md for why this volume (233 lines) is classified
    this way instead."""
    s = source_line.upper()
    a = alias.upper()
    if re.search(r"^\s*\d*\s*(FILLER\s+)?REDEFINES\b", s) or re.search(r"\bPIC\b", s) and "MOVE" not in s and "TO " not in s:
        return "DECLARATION"
    if re.search(r"RIDFLD|RECORD KEY IS|KEYLENGTH", s):
        return "READ"
    if "DISPLAY" in s:
        return "DISPLAY"
    if re.search(r"\bIF\b|\bEQUAL\b|\bWHEN\b", s):
        return "COMPARE"
    mv = re.search(r"MOVE\s+(.*?)\s+TO\s+(.*)", s)
    if mv:
        src, tgt = mv.group(1), mv.group(2)
        if a in src and a not in tgt:
            return "MOVE-SOURCE"
        if a in tgt:
            return "MOVE-TARGET"
    if " TO " in s and s.strip().endswith(a):
        return "MOVE-TARGET (continuation)"
    return "UNCLASSIFIED (wrapped statement -- see source_line, needs manual read)"


def apply_2026_08_29_reclassification(wide_result):
    """Second, explicit transformation pass over build_wide()'s original
    output. Does not alter the original extraction/classification data --
    reads the near_misses list it already produced (itself built from the
    unmodified extractor) and re-buckets each identifier's lines per
    ALIAS_VERDICTS, verified against source in the 2026-08-29 review."""
    by_prog_new_hits = collections.defaultdict(lambda: collections.defaultdict(list))
    remaining_near_miss = []
    excluded_uncertain = []

    for nm in wide_result["near_misses"]["distinct_identifiers"]:
        ident = nm["identifier"]
        verdict = ALIAS_VERDICTS.get(ident)
        if verdict is None:
            raise SystemExit(f"UNCLASSIFIED IDENTIFIER in reclassification pass: {ident}")

        if verdict == "dead":
            remaining_near_miss.append(nm)
            continue

        if verdict == "alias":
            for prog in nm["programs"]:
                for line in prog["lines"]:
                    by_prog_new_hits[prog["path"]][ident].append(line)
            continue

        # per-program split
        dead_programs = []
        for prog in nm["programs"]:
            prog_key = prog["path"].split("/")[-1]
            pverdict = verdict.get(prog_key)
            if pverdict is None:
                raise SystemExit(f"UNCLASSIFIED PROGRAM for split identifier: {ident} / {prog['path']}")
            if pverdict == "alias":
                for line in prog["lines"]:
                    by_prog_new_hits[prog["path"]][ident].append(line)
            elif pverdict == "dead":
                dead_programs.append(prog)
            elif pverdict == "excluded":
                excluded_uncertain.append({
                    "identifier": ident, "path": prog["path"], "lines": prog["lines"],
                    "reason": "fed by WS-KEY, itself never assigned via any MOVE in this file -- plausible but unprovable",
                })
        if dead_programs:
            remaining_near_miss.append({
                "identifier": ident,
                "total_occurrences": sum(len(p["lines"]) for p in dead_programs),
                "programs": dead_programs,
            })

    # Attach new alias hits to programs, upgrading tier where needed.
    existing_paths = {p["path"]: p for p in wide_result["programs"]}
    for path, alias_lines in by_prog_new_hits.items():
        alias_hit_entries = []
        for ident, lines in sorted(alias_lines.items()):
            lines_sorted = sorted(set(lines))
            alias_hit_entries.append({
                "alias": ident,
                "lines": lines_sorted,
                "evidence": ALIAS_EVIDENCE.get(ident, ""),
                "classification_method": "automated pattern match on source_line text per line; see reference note in CHANGELOG.md",
            })
        if path in existing_paths:
            prog = existing_paths[path]
            prog["alias_hits"] = alias_hit_entries
            if prog["tier"] != "FIELD-AWARE":
                prog["tier_before_reclassification"] = prog["tier"]
                prog["tier"] = "FIELD-AWARE"
                # structural_evidence (or dead_copy_evidence) is intentionally left in
                # place -- it's still true and still useful context, just no longer
                # the reason for the tier.
        else:
            # Program had no entry at all before (shouldn't happen for the wide
            # field slice, since all 21 programs are covered, but guard anyway)
            raise SystemExit(f"Alias hits found for a program not in the original tiered list: {path}")

    wide_result["programs"].sort(key=lambda p: (p["module"], p["path"]))

    new_near_miss_total = sum(nm["total_occurrences"] for nm in remaining_near_miss)
    wide_result["near_misses"]["distinct_identifiers"] = remaining_near_miss
    wide_result["near_misses"]["summary"] = (
        f"After the 2026-08-29 alias-rule reclassification (see docs/ground_truth/CHANGELOG.md), "
        f"{new_near_miss_total} lines across {len(remaining_near_miss)} distinct identifiers remain "
        "genuine near misses -- declared but demonstrably never fed by anything, dead code rather "
        "than a different entity. This is the precision test set: a tool should find zero of these."
    )

    wide_result["excluded_from_scoring"] = {
        "summary": (
            f"{sum(len(e['lines']) for e in excluded_uncertain)} lines, from WS-CARD-RID-ACCT-ID and "
            "its -X redefine in COACCT01.cbl, are excluded from both the true-positive and "
            "false-positive count. Plausible (labeled 'ACCT ID' in a DISPLAY, used identically to "
            "confirmed alias-fed keys elsewhere) but not provable from an explicit MOVE within this "
            "file alone -- scoring them either way would misrepresent what was actually verified."
        ),
        "entries": excluded_uncertain,
    }

    wide_result["definitions"] = {
        "adopted": "2026-08-29",
        "supersedes": "the original near-miss-by-substring-only classification used through 2026-08-28",
        "rule": (
            "A field is an ALIAS of the target if the target's value flows into it via an "
            "explicit MOVE (either direction -- both operands must co-widen together or the "
            "narrower one truncates at runtime), or if it REDEFINES a field that is itself "
            "alias-confirmed (same storage, so any MOVE feeding one feeds both). A field is a "
            "NEAR MISS only if it is a genuinely different entity -- different data, different "
            "meaning -- regardless of name similarity. A field that is declared but demonstrably "
            "never fed by anything is also a near miss (dead code, not a different entity -- just "
            "no entity)."
        ),
        "read_into_extension": (
            "2026-08-29 extension: a field fed by a whole-record READ ... INTO from a record "
            "that contains the target field is also an ALIAS, even with no field-level MOVE "
            "naming it. Rationale: widening the source record's field requires widening the "
            "receiving record's corresponding field too, or the READ misaligns/truncates on that "
            "field -- the identical risk a literal MOVE poses, via positional record I/O instead "
            "of a field-level statement."
        ),
        "excluded_from_scoring_rule": (
            "A candidate that is plausibly fed by the target but whose feed cannot be traced to "
            "an explicit MOVE from the target or a confirmed alias within the file being checked "
            "is EXCLUDED FROM SCORING entirely -- counted as neither a true positive nor a false "
            "positive -- rather than guessed either way."
        ),
    }
    return wide_result


# ---------------------------------------------------------------------------
# FIELD 2: ACCT-ADDR-ZIP (narrow) -- near miss CUST-ADDR-ZIP
# ---------------------------------------------------------------------------

ZIP_TARGETS = ["ACCT-ADDR-ZIP", "CUST-ADDR-ZIP"]

ZIP_HIT_NOTES = {
    ("cbl/CBEXPORT.cbl", 361, "ACCT-ADDR-ZIP"): ("MOVE-SOURCE", "copied into EXP-ACCT-ADDR-ZIP, the branch-migration export record"),
    ("cbl/CBIMPORT.cbl", 338, "ACCT-ADDR-ZIP"): ("MOVE-TARGET", "received from EXP-ACCT-ADDR-ZIP -- reverse of CBEXPORT.cbl:361"),
}

# Programs that actively COPY CVACT01Y but have zero exact ACCT-ADDR-ZIP hits:
# verified structural evidence (whole-group I/O touching ACCOUNT-RECORD).
ZIP_STRUCTURAL = {
    "cbl/CBACT01C.cbl": [{"line": 166, "source_line": "READ ACCTFILE-FILE INTO ACCOUNT-RECORD."}],
    "cbl/CBACT04C.cbl": [{"line": 373, "source_line": "READ ACCOUNT-FILE INTO ACCOUNT-RECORD"},
                          {"line": 356, "source_line": "REWRITE FD-ACCTFILE-REC FROM  ACCOUNT-RECORD"}],
    "cbl/CBTRN01C.cbl": [{"line": 243, "source_line": "READ ACCOUNT-FILE RECORD INTO ACCOUNT-RECORD"}],
    "cbl/CBTRN02C.cbl": [{"line": 395, "source_line": "READ ACCOUNT-FILE INTO ACCOUNT-RECORD"},
                          {"line": 554, "source_line": "REWRITE FD-ACCTFILE-REC FROM  ACCOUNT-RECORD"}],
    "cbl/CBSTM03A.CBL": [{"line": 412, "source_line": "MOVE WS-M03B-FLDT TO ACCOUNT-RECORD."}],
    "cbl/COACTVWC.cbl": [{"line": 780, "source_line": "INTO      (ACCOUNT-RECORD)"},
                          {"line": 781, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
    "cbl/COACTUPC.cbl": [{"line": 3707, "source_line": "INTO      (ACCOUNT-RECORD)"},
                          {"line": 3708, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"},
                          {"line": 3899, "source_line": "INTO      (ACCOUNT-RECORD)"},
                          {"line": 3900, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
    "cbl/COBIL00C.cbl": [{"line": 347, "source_line": "INTO      (ACCOUNT-RECORD)"},
                         {"line": 348, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"},
                         {"line": 381, "source_line": "FROM      (ACCOUNT-RECORD)"},
                         {"line": 382, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
    "app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl": [{"line": 873, "source_line": "INTO      (ACCOUNT-RECORD)"},
                                                       {"line": 874, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
    "app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl": [{"line": 529, "source_line": "INTO      (ACCOUNT-RECORD)"},
                                                       {"line": 530, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
    "app-vsam-mq/cbl/COACCT01.cbl": [{"line": 400, "source_line": "INTO      (ACCOUNT-RECORD)"},
                                      {"line": 401, "source_line": "LENGTH    (LENGTH OF ACCOUNT-RECORD)"}],
}

# Modules for the programs referenced only in ZIP_STRUCTURAL (not covered by
# the extraction pass's field-aware set below) -- keep in sync with
# ground_truth_extract.PROGRAMS.
ZIP_MODULE = {
    "cbl/CBACT01C.cbl": "core", "cbl/CBACT04C.cbl": "core", "cbl/CBTRN01C.cbl": "core",
    "cbl/CBTRN02C.cbl": "core", "cbl/CBSTM03A.CBL": "core", "cbl/COACTVWC.cbl": "core",
    "cbl/COACTUPC.cbl": "core", "cbl/COBIL00C.cbl": "core",
    "app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl": "optional",
    "app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl": "optional",
    "app-vsam-mq/cbl/COACCT01.cbl": "optional",
    "cbl/COTRN02C.cbl": "core",
}

ZIP_DEAD_COPY = {
    "cbl/COTRN02C.cbl": {
        "copybook": "CVACT01Y", "record": "ACCOUNT-RECORD", "copy_line": 89,
        "note": (
            "Same underlying finding as recorded for the wide field: COTRN02C.cbl "
            "has an active COPY CVACT01Y but never references ACCOUNT-RECORD or any "
            "ACCT-* field anywhere else in the file. For ACCT-ADDR-ZIP specifically, "
            "this program has no other copybook that could make it relevant, so its "
            "whole relationship to this field is DEAD-COPY (unlike the wide field, "
            "where this program is FIELD-AWARE via a different copybook)."
        ),
    },
}

ZIP_UNCERTAIN = []


def build_zip():
    data = run_extract(*ZIP_TARGETS)
    programs_out = []
    field_aware_paths = set()

    for path, pdata in data.items():
        exact_hits = [h for h in pdata["hits"]
                      if h["match_type"] == "exact" and not h["in_string_literal"]
                      and h["matched_target"] == "ACCT-ADDR-ZIP"]
        if exact_hits:
            field_aware_paths.add(path)
            hit_entries = []
            for h in exact_hits:
                key = (path, h["line"], h["matched_target"])
                if key not in ZIP_HIT_NOTES:
                    raise SystemExit(f"UNCLASSIFIED HIT (fix ZIP_HIT_NOTES): {key} -> {h['source_line']}")
                access_kind, note = ZIP_HIT_NOTES[key]
                hit_entries.append({
                    "alias": h["matched_target"],
                    "line": h["line"],
                    "access_kind": access_kind,
                    "source_line": h["source_line"],
                    "note": note,
                })
            hit_entries.sort(key=lambda x: x["line"])
            programs_out.append({
                "path": path, "module": pdata["module"], "tier": "FIELD-AWARE", "hits": hit_entries,
            })

    for path, evidence in ZIP_STRUCTURAL.items():
        if path in field_aware_paths:
            continue
        programs_out.append({
            "path": path,
            "module": ZIP_MODULE[path],
            "tier": "STRUCTURALLY-AFFECTED",
            "hits": [],
            "structural_evidence": [{"copybook": "CVACT01Y", "record": "ACCOUNT-RECORD", "evidence": evidence}],
        })

    for path, entry in ZIP_DEAD_COPY.items():
        if path in field_aware_paths or path in ZIP_STRUCTURAL:
            continue
        programs_out.append({
            "path": path,
            "module": ZIP_MODULE[path],
            "tier": "DEAD-COPY",
            "hits": [],
            "dead_copy_evidence": [entry],
        })

    # near misses: every CUST-ADDR-ZIP hit (exact only -- this is a real,
    # distinct, declared field, not a derived shadow variable, so no
    # substring-vs-exact split is needed the way it was for the wide field)
    near_miss_hits = []
    for path, pdata in data.items():
        for h in pdata["hits"]:
            if h["matched_target"] == "CUST-ADDR-ZIP" and h["match_type"] == "exact" and not h["in_string_literal"]:
                near_miss_hits.append({"path": path, "module": pdata["module"], "line": h["line"], "source_line": h["source_line"]})
    near_miss_hits.sort(key=lambda x: (x["path"], x["line"]))

    # also report the *derived* CUST-ADDR-ZIP shadow variables (substring hits)
    # as a secondary, weaker near-miss signal for completeness
    by_token = collections.defaultdict(list)
    for path, pdata in data.items():
        for h in pdata["hits"]:
            if h["match_type"] == "substring" and h["token"].upper() not in {"ACCT-ADDR-ZIP", "CUST-ADDR-ZIP"}:
                by_token[h["token"].upper()].append({"path": path, "line": h["line"]})
    derived_near_misses = []
    for tok in sorted(by_token, key=lambda t: -len(by_token[t])):
        locs = by_token[tok]
        by_prog = collections.defaultdict(list)
        for loc in locs:
            by_prog[loc["path"]].append(loc["line"])
        derived_near_misses.append({
            "identifier": tok,
            "total_occurrences": len(locs),
            "programs": [{"path": p, "lines": sorted(ls)} for p, ls in sorted(by_prog.items())],
        })

    programs_out.sort(key=lambda p: (p["module"], p["path"]))

    result = {
        "field": "ACCT-ADDR-ZIP (narrow)",
        "field_definition": {"copybook": "CVACT01Y", "record": "ACCOUNT-RECORD", "pic": "X(10)"},
        "tier_definitions": {
            "FIELD-AWARE": "names the exact token ACCT-ADDR-ZIP somewhere in its own code, outside of string literals",
            "STRUCTURALLY-AFFECTED": "COPYs CVACT01Y and performs whole-group I/O on ACCOUNT-RECORD, but never names ACCT-ADDR-ZIP itself",
            "DEAD-COPY": "COPYs CVACT01Y but never touches ACCOUNT-RECORD at all -- not by field name, not even at group level. Real technical debt the tool surfaces for free.",
        },
        "methodology": (
            "Same extraction method as the wide field (scripts/ground_truth_extract.py), "
            "scoped to the 14 programs that actively COPY CVACT01Y (the only copybook "
            "declaring ACCT-ADDR-ZIP) among the 21-program slice. Programs that never "
            "COPY CVACT01Y are correctly absent from this file -- they cannot be "
            "affected by this field at all."
        ),
        "programs": programs_out,
        "near_misses": {
            "primary": {
                "identifier": "CUST-ADDR-ZIP",
                "copybook": "CVCUS01Y",
                "record": "CUSTOMER-RECORD",
                "pic": "X(10)",
                "summary": (
                    "CUST-ADDR-ZIP is a real, distinct, declared field (customer address "
                    "zip, not account address zip) that happens to share the exact same "
                    "PIC X(10) shape and a 'zip code' natural-language description. A "
                    "naive grep for 'zip' or even 'ADDR-ZIP' returns this as a false "
                    "positive for an ACCT-ADDR-ZIP change request. It is genuinely "
                    "declared in CVCUS01Y, outside the CVACT01Y/02Y/03Y slice, so its "
                    "affected-program list was pulled from the same 21-program search, "
                    "not assumed."
                ),
                "hits": near_miss_hits,
            },
            "secondary_derived_shadow_variables": derived_near_misses,
        },
        "uncertain": ZIP_UNCERTAIN,
    }
    return result


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    wide = build_wide()
    wide = apply_2026_08_29_reclassification(wide)
    zip_ = build_zip()
    with open(os.path.join(OUT_DIR, "ACCT-ID.json"), "w") as f:
        json.dump(wide, f, indent=2)
        f.write("\n")
    with open(os.path.join(OUT_DIR, "ACCT-ADDR-ZIP.json"), "w") as f:
        json.dump(zip_, f, indent=2)
        f.write("\n")
    print("wrote docs/ground_truth/ACCT-ID.json and docs/ground_truth/ACCT-ADDR-ZIP.json")

    fa = sum(1 for p in wide["programs"] if p["tier"] == "FIELD-AWARE")
    sa = sum(1 for p in wide["programs"] if p["tier"] == "STRUCTURALLY-AFFECTED")
    dc = sum(1 for p in wide["programs"] if p["tier"] == "DEAD-COPY")
    footnotes = sum(1 for p in wide["programs"] if p.get("dead_copy_footnotes"))
    print(f"ACCT-ID (wide): FIELD-AWARE={fa} STRUCTURALLY-AFFECTED={sa} DEAD-COPY={dc} "
          f"(+{footnotes} dead-copy footnote(s) on otherwise-tiered programs) "
          f"UNCERTAIN={len(wide['uncertain'])} TOTAL={fa+sa+dc}")
    print(f"  near-miss distinct identifiers={len(wide['near_misses']['distinct_identifiers'])} "
          f"total lines={sum(n['total_occurrences'] for n in wide['near_misses']['distinct_identifiers'])}")

    fa2 = sum(1 for p in zip_["programs"] if p["tier"] == "FIELD-AWARE")
    sa2 = sum(1 for p in zip_["programs"] if p["tier"] == "STRUCTURALLY-AFFECTED")
    dc2 = sum(1 for p in zip_["programs"] if p["tier"] == "DEAD-COPY")
    print(f"ACCT-ADDR-ZIP (narrow): FIELD-AWARE={fa2} STRUCTURALLY-AFFECTED={sa2} DEAD-COPY={dc2} "
          f"UNCERTAIN={len(zip_['uncertain'])} TOTAL={fa2+sa2+dc2}")
    print(f"  near-miss CUST-ADDR-ZIP exact hits={len(zip_['near_misses']['primary']['hits'])}")


if __name__ == "__main__":
    main()
