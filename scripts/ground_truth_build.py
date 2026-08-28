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

    # near misses: distinct locally-derived identifiers, not the true aliases
    true_targets_upper = {t.upper() for t in WIDE_TARGETS}
    by_token = collections.defaultdict(list)
    for path, pdata in data.items():
        for h in pdata["hits"]:
            if h["match_type"] == "substring" and h["token"].upper() not in true_targets_upper:
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
