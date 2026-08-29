# Artifact file layout and schemas

All working files live under `.blast-radius/` at the workspace root
(this is the CardDemo sample root when this skill is run as designed —
never write inside `app/`, only under `.blast-radius/`).

```
.blast-radius/
  artifacts/
    inventory.json          -- INVENTORY output (whole-repo file/symbol index)
    spec-<field-slug>.json  -- SPEC output (resolved field + aliases)
    trace-<field-slug>-group-<N>.json   -- one per TRACE subagent group
    verified-<field-slug>.json          -- VERIFY output (merged + judged)
  reports/
    <field-slug>-impact-report.html     -- SYNTHESIS final output
```

`<field-slug>` is the target field name lowercased with non-alphanumerics
turned into hyphens (e.g. `ACCT-ID` -> `acct-id`).

## inventory.json (INVENTORY stage)

```json
{
  "generated_at": "ISO-8601 timestamp -- from `date -u +\"%Y-%m-%dT%H:%M:%SZ\"`, run fresh, never fabricated or reused from another artifact",
  "scope": "path walked, e.g. app/",
  "file_counts_by_extension": {".cbl": 0, ".cpy": 0, ".jcl": 0, ".bms": 0},
  "programs": [
    {"path": "...", "module": "core" | "optional", "type": "batch" | "online-cics" | "other"}
  ],
  "copybooks": [
    {"name": "CVACT01Y", "path": "cpy/CVACT01Y.cpy", "records": ["ACCOUNT-RECORD"]}
  ],
  "copy_graph": [
    {"program": "cbl/CBACT01C.cbl", "copybook": "CVACT01Y", "active": true, "line": 89}
  ],
  "call_graph": [
    {"caller": "cbl/COACTUPC.cbl", "callee": "...", "mechanism": "CICS-XCTL" | "CICS-LINK" | "CALL", "line": 0}
  ]
}
```

`copy_graph` entries must respect COBOL column 7: a commented-out COPY
statement is `"active": false` and should still be recorded (it's useful
signal — code that once depended on something and no longer does), not
silently dropped.

## spec-<field-slug>.json (SPEC stage)

```json
{
  "change_request": "the user's plain-language request, verbatim",
  "resolved_field": "ACCT-ID",
  "aliases": [
    {"name": "ACCT-ID", "copybook": "CVACT01Y", "record": "ACCOUNT-RECORD", "pic": "9(11)"},
    {"name": "CARD-ACCT-ID", "copybook": "CVACT02Y", "record": "CARD-RECORD", "pic": "9(11)"}
  ],
  "candidate_programs": ["cbl/CBACT01C.cbl", "..."],
  "resolution_notes": "how the plain-language phrase was matched to these field names"
}
```

`candidate_programs` is every program in `inventory.json`'s `copy_graph`
whose copybook matches one of the resolved aliases (active COPY only) --
this list is what gets split into TRACE groups of 3-5.

## trace-<field-slug>-group-<N>.json (TRACE stage, one file per subagent)

Exactly the schema in `program-tracer.md`'s Output section: a top-level
`{"programs": [...]}` array. Nothing else needed here; see that file for
the per-program shape.

## verified-<field-slug>.json (VERIFY stage)

Exactly the schema in `hit-verifier.md`'s Output section
(`{"verdicts": [...], "alias_verdicts": [...], "summary": {...}}`), plus a
final merged view the orchestrator builds by joining verdicts back onto
the TRACE claims (fold every ACCEPTED `alias_verdicts` entry into the
alias list the same as any other confirmed alias):

```json
{
  "verdicts": [ /* as produced by hit-verifier */ ],
  "summary": { /* as produced by hit-verifier */ },
  "final_programs": [
    {
      "path": "...", "module": "core" | "optional", "tier": "...",
      "hits": [ /* only ACCEPTED hits, with corrected_access_kind applied */ ],
      "risk_score": 0
    }
  ]
}
```

## Risk score (computed during SYNTHESIS, not by TRACE or VERIFY)

Deterministic formula, applied per program in `final_programs`:

```
base = 30 if tier == FIELD-AWARE else 10 if tier == STRUCTURALLY-AFFECTED else 2  (DEAD-COPY)
access_weight = sum over accepted hits of:
    WRITE=8, MOVE-TARGET=6, PASSED-TO-PROGRAM=6, COMPARE=5,
    MOVE-SOURCE=4, READ=3, DISPLAY=1
module_multiplier = 1.0 if module == "core" else 0.7 if module == "optional"
risk_score = round((base + access_weight) * module_multiplier)
```

This is a stated, reproducible formula, not a judgment call per program --
apply it mechanically so two runs produce the same ranking for the same
verified data. Sort the final report's program table by `risk_score`
descending.
