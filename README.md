# Blast Radius

A change-impact analyzer for legacy IBM i / IBM Z codebases (COBOL, RPG,
CL, JCL, DDS, copybooks), built as an **IBM Bob IDE** package for the IBM
TechXchange 2026 Pre-conference Dev Day Hackathon.

## The problem

A developer gets a change request like *"extend the customer number field"*
or *"add a status code to the order file."* Before writing any code they
must find every program, copybook, display file, report, and job that
touches that field. In a legacy estate this is manual grep-and-pray work
that takes hours to days, and missing one caller causes a production
incident. Naive text search makes this worse, not better: it misses real
aliases (the business calls it "account ID," the code spells it three
different ways across three copybooks) and it drowns you in false
positives (a working-storage variable that merely *contains* the field
name as a naming convention is not the field).

## What Blast Radius does

Given a target field and a plain-language change request, it produces an
impact report: every affected program, tiered by how it's actually
affected, ranked by risk, with a dependency graph — and it does this
*inside* IBM Bob, using Bob's own agentic tool use (reading files, running
shell commands it constructs itself, spawning subagents), not a
standalone script that merely calls an LLM API.

**Five-stage pipeline**, all running as a single Bob Skill:

1. **INVENTORY** — walks the entire sample application, classifies source
   files, and builds a copybook/COPY-graph and call-graph index. Runs once
   per session, cached.
2. **SPEC** — resolves the plain-language change request to the actual
   field name(s), including every alias across sibling copybooks, by
   reading the copybooks directly (not guessing from the phrase alone).
3. **TRACE** — subagents in parallel, each given a small group of 3-5
   candidate programs, determine how that group touches the field and at
   which tier.
4. **VERIFY** — an independent subagent re-checks every claimed hit
   against the real source: COBOL column-7 comment rules, string-literal
   spans, and exact-token-vs-substring matching. This is the precision
   gate — the near-miss numbers below exist because of this stage.
5. **SYNTHESIS** — merges verified results, computes a deterministic risk
   score, and renders a single self-contained HTML report.

Full design and every prompt: [`bob-package/`](bob-package/) (canonical,
version-controlled) — see [`bob-package/README.md`](bob-package/README.md)
for how it's deployed into the actual Bob workspace and run.

**Why Bob is the core component, not a wrapper around one:** the
column-7/string-literal/exact-token discipline that makes this precise is
taught to the personas as *method*, in plain instructions — not handed to
them as a finished script they execute blind. Bob's subagents write their
own `sed`/`awk`/`grep` as part of their own reasoning, the same way a
person would actually do this analysis by hand.

## The sample codebase: CardDemo

Analysis runs against
[aws-samples/aws-mainframe-modernization-carddemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo)
(Apache License 2.0), AWS's reference COBOL mainframe-modernization
application. Full copy vendored at [`samples/carddemo/`](samples/carddemo/)
under its original license (`samples/carddemo/LICENSE`), ~39 COBOL
programs, ~62 copybooks, ~46 JCL jobs, ~21 BMS screen maps, ~49,500 LOC
across the core application and optional IMS/DB2/MQ integration modules.

### Scoping decision

Hand-verifying a trace across the full ~130-file application isn't
feasible in a hackathon timebox, so the **ground truth** (the hand-built
answer key this project's accuracy claim rests on) is scoped to one
vertical slice: every program that `COPY`s `CVACT01Y` (account record),
`CVACT02Y` (card record), or `CVACT03Y` (card cross-reference record) —
**21 programs** (17 core, 4 optional-integration-module). The pipeline's
own INVENTORY stage still walks the *entire* application, so the tool is
demonstrated at realistic scale; only the answer key used to score it is
scoped down to something a human can verify by hand. Full rationale,
including a correction to an earlier miscount, in
[`docs/SCOPE.md`](docs/SCOPE.md).

## Key finding: hand-verified ground truth measures agentic analysis, end to end

A full pipeline run (SPEC through SYNTHESIS, core programs, change request
*"extend the account identifier field"*), scored against the hand-verified
ground truth: **100% program-level recall (17/17 core programs found),
100% tier accuracy, and 100% alias-level recall against the documented
ground truth (25/25) — plus 7 additional real aliases found beyond it**,
independently re-verified against source. One real gap was found and is
reported plainly rather than smoothed over: near-miss (dead-code)
coverage was 9/14 on one identifier family, not 14/14 — an omission, not
a false claim. Full derivation of every number: **[`docs/ACCURACY.md`](docs/ACCURACY.md).**

This result followed directly from an earlier, worse one. A SPEC-only
run against the same change request found 8 real aliases (100%
precision) out of a documented true count of at least 28 (recall ≈
28.6%) and the gap turned out to be partly *instructed*: the TRACE and
VERIFY persona prompts encoded the same "different token means near
miss" mistake the ground truth itself had to unlearn. Fixing that
persona bug, then re-running the full pipeline, is what produced the
result above. Full story, the exact failure mode, and the fix:
**[`docs/FINDINGS.md`](docs/FINDINGS.md).**

This is the case for why the pipeline doesn't stop at SPEC — TRACE
independently inspects every candidate program's own body for exactly
this kind of local MOVE chain, and VERIFY re-checks every claim regardless
of which stage produced it. It's also a case for treating a bad first
number as diagnostic rather than embarrassing: it pointed directly at the
bug that, once fixed, produced the number above.

## Ground truth: the answer key

**[`docs/ground_truth/`](docs/ground_truth/)** is deliberately public —
judges should be able to verify every accuracy claim against it directly.
It is hidden from Bob itself (see below), not from people.

Two fields were traced exhaustively by hand, line by line, every hit
checked against COBOL column 7 and string-literal boundaries. The
`ACCT-ID` figures below reflect the alias reclassification described in
[`docs/ground_truth/CHANGELOG.md`](docs/ground_truth/CHANGELOG.md) a
field genuinely fed by the target's value via an explicit MOVE (or a
whole-record READ from a record containing it) counts as an alias, not a
near miss, because widening the target requires widening it too:

| Field | Aliases | Scope | FIELD-AWARE | STRUCTURALLY-AFFECTED | DEAD-COPY | Near misses (precision test set) |
|---|---|---|---|---|---|---|
| `ACCT-ID` (wide) | 3 declared names + 27 confirmed aliases (commarea/work-area/FD carriers fed by an explicit MOVE or record-level READ) | 21 programs | 18 | 2 | 1 | 6 distinct identifiers, 23 lines — genuinely dead code, never fed by anything |
| `ACCT-ADDR-ZIP` (narrow) | single field, one copybook | 14 programs (only those copying `CVACT01Y`) | 2 | 11 | 1 | `CUST-ADDR-ZIP`, a distinct customer-level field: 7 exact hits, 6 programs |

Three tiers, not two: **FIELD-AWARE** (names the field or a confirmed alias
directly), **STRUCTURALLY-AFFECTED** (copies the copybook and moves the
whole record, but never names the field or an alias), and **DEAD-COPY**
(copies the copybook but never touches the resulting record at all — real
technical debt the analysis surfaces for free). Every hit is reproducible
from [`scripts/ground_truth_extract.py`](scripts/ground_truth_extract.py)
(a COBOL-column-7-aware, string-literal-aware tokenizer) plus verified
classification in
[`scripts/ground_truth_build.py`](scripts/ground_truth_build.py) — re-run
`python3 scripts/ground_truth_build.py` to regenerate both JSON files from
scratch and confirm they match what's committed. 6 additional lines (two
identifiers, both only in `COACCT01.cbl`) are recorded as **excluded from
scoring** — plausible but not provable from an explicit MOVE within that
file, so counted as neither a true positive nor a false positive rather
than guessed either way.

### Hidden from Bob, visible to everyone else

Bob's entire value proposition here is finding this independently. Three
layers keep the answer key out of its reach without hiding it from anyone
reviewing this repo:

1. **Isolated workspace root** — Bob is opened on `samples/carddemo/`
   directly, not this repo's root. `docs/ground_truth/` is a sibling of
   `samples/`, structurally outside the tree Bob can traverse from there —
   not hidden, physically unreachable.
2. **`.bobignore`** at this repo's root, in case Bob is ever pointed at the
   parent folder instead.
3. **An explicit rule file** (`bob-package/.bob/rules/`), loaded in every
   mode, telling Bob never to read that path even if it became reachable.

## Repository layout

```
samples/carddemo/          -- vendored CardDemo application (Apache 2.0) + the live Bob workspace
  .bob/                    -- deployed Bob package (see bob-package/, the canonical source)
  app/                     -- the COBOL/JCL/BMS/copybook source being analyzed
docs/
  SCOPE.md                 -- scoping rationale, slice definition, field selection
  FINDINGS.md              -- the SPEC-only measurement, the persona bug it found, and the fix
  ACCURACY.md              -- the centerpiece: full-pipeline run scored against ground truth
  ground_truth/            -- the hand-verified answer key (public; hidden from Bob only)
    CHANGELOG.md           -- the 2026-08-29 alias-rule reclassification, with rationale
bob-package/                -- canonical Bob Skill + personas + custom mode (read this to review the design)
bob_sessions/               -- raw Bob task transcripts backing FINDINGS.md/ACCURACY.md's claims
scripts/
  ground_truth_extract.py  -- deterministic COBOL tokenizer (column-7 + string-literal aware)
  ground_truth_build.py    -- assembles docs/ground_truth/*.json from the extractor + verified classifications
  score_run.py             -- scores a completed Bob run against ground truth (docs/ACCURACY.md)
  survey_slice.sh          -- reproduces the slice-selection survey from docs/SCOPE.md
  bob_sync_push.sh         -- deploys bob-package/.bob into samples/carddemo/.bob (what Bob actually reads)
  bob_sync_pull.sh         -- brings a completed run's report + artifacts back out of the isolated workspace
reports/                   -- pulled-out HTML impact reports land here after a run
```

## How to run it

```
scripts/bob_sync_push.sh
```

Then open **`samples/carddemo/`** as its own folder in Bob IDE (2.0.3) —
not this repo's root — switch to the **Blast Radius** custom mode, and
describe a change request, e.g. *"I want to extend the account ID field —
what's affected?"* Bob runs all five stages and writes a report to
`samples/carddemo/.blast-radius/reports/`. Bring it back into this repo
with:

```
scripts/bob_sync_pull.sh
```

Full design notes, cost-discipline decisions (a 40-Bobcoin budget shaped
the small-group parallel TRACE dispatch and the fixed-template report), and
every persona prompt: [`bob-package/README.md`](bob-package/README.md).

## License

CardDemo (`samples/carddemo/`) is Apache License 2.0, © Amazon.com, Inc. or
its affiliates — see `samples/carddemo/LICENSE`. Everything else in this
repository is the hackathon submission itself.
