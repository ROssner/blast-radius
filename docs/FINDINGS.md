# Findings: what hand-verified ground truth reveals about agentic impact analysis

This is the central claim of this submission. Every number here is checkable
against [`docs/ground_truth/ACCT-ID.json`](ground_truth/ACCT-ID.json), its
[`CHANGELOG.md`](ground_truth/CHANGELOG.md), [`docs/ACCURACY.md`](ACCURACY.md)
(the full scoring detail behind the current headline below), and the raw Bob
session output in [`bob_sessions/`](../bob_sessions/) — both the SPEC-only run
(`blastradius_task01_inventory.json` is INVENTORY-only; the SPEC-only
measurement below came from a separate task not saved as its own export at
the time) and the full pipeline run
(`blastradius_task02_full_pipeline.json`). Nothing here is an estimate.

## Current headline (2026-08-29): the full pipeline, measured

A completed run of the full pipeline — SPEC through SYNTHESIS, core
programs only, the corrected personas described in the postscript below —
scored against the same ground truth:

- **Program-level recall: 17/17 = 100%.** Every core program in the ground
  truth was found.
- **Tier accuracy: 17/17 = 100%.** Including the three hardest cases in
  the whole ground truth (`COACTVWC.cbl`, `COCRDSLC.cbl`, `COCRDUPC.cbl`),
  where Bob independently reached the tier that only changed in this
  project's own 2026-08-29 alias reclassification.
- **Alias-level recall: 25/25 = 100%** against the documented ground
  truth, plus **7 additional real aliases found beyond it** — independently
  verified against source, not taken on trust.
- **Near-miss precision: 9/14 identifier-program pairs correctly flagged
  as dead code; 5/14 a silent gap** (one identifier family,
  `WS-CARD-RID-ACCT-ID`/`-X`, in two of three relevant programs) — not a
  false claim, an omission. Reported plainly rather than rounded up to
  "solved."

Full breakdown, every number's derivation, and the one imperfection found:
[`docs/ACCURACY.md`](ACCURACY.md). **This is the current, load-bearing
number for this submission.** The rest of this document, below, is the
SPEC-only measurement that came first, and the story of what it led to —
kept in full because the persona-prompt bug it surfaced, and the fix that
followed, is itself the more interesting finding, not something to delete
now that the number looks better.

## Where this started: the SPEC-only measurement

Running the `blast-radius` Skill's SPEC stage alone in Bob against the change
request *"extend the account identifier field to support longer account
numbers"*, Bob resolved the target field and searched for its aliases. It
found **8**. It cited a specific `MOVE` bridge for each one.

**All 8 are correct.** Every citation was independently re-verified against
source — same discipline as the rest of this ground truth: column 7 checked,
string literals excluded, exact tokens confirmed. **Precision: 8/8 = 100%.**

**The true count of aliases is at least 28.** Bob found 8 of them.
**Recall: 8/28 ≈ 28.6%.**

Precision and recall this far apart, both measured against a real answer
key, is the finding. A tool that is *always right when it speaks* but
*silently quiet most of the time it should have spoken* is dangerous in a
specific way: it doesn't look wrong. Every one of Bob's 8 findings would
survive a spot check. Nothing about the SPEC output signals that 20 more
fields needed to change.

## The pattern: not random, not a handful of edge cases — one clean rule

Categorizing all 28 aliases by where they're declared:

| Declaration site | Count | Bob found | Recall |
|---|---|---|---|
| Shared copybook (`CVCRD01Y`, `COCOM01Y`, `CVTRA01Y`, `CVTRA07Y`, `CVEXPORT`) | 8 | **8** | **100%** |
| Locally declared per program (WORKING-STORAGE or FD SECTION, not COPYed) | 20 | **0** | **0%** |

This split is exact — not "mostly," not "with a few exceptions." Every
single alias Bob found is declared in a shared copybook. Every single alias
Bob missed is declared locally inside one specific program's own
WORKING-STORAGE or FD SECTION.

The reason is visible in the SPEC stage's own design
([`bob-package/.bob/skills/blast-radius/SKILL.md`](../bob-package/.bob/skills/blast-radius/SKILL.md),
Stage 2): it instructs reading the copybooks to resolve aliases, and gives
MOVE-bridge evidence as the *confirming* signal, not the *search* method.
Bob followed that literally — it read the copybooks CardDemo declares
account-shaped fields in, found genuine bridges into commarea and other
shared structures from there, and stopped. It never appears to have traced
MOVE chains *within* an individual program's own body looking for local
derived copies with no copybook of their own. That is a real, nameable gap
in the SPEC design, not an occasional model slip — and it's fixable: the
skill should explicitly instruct tracing every MOVE touching a
confirmed-alias field, inside every candidate program's own body, not only
reading copybooks.

## The concrete example: one file, four misses, all in five lines

`app/cbl/CBACT01C.cbl` ("read the account file and write into files," per
its own header comment) copies `ACCT-ID` out into four differently-shaped
output records in the space of about 60 lines:

```
216:           MOVE   ACCT-ID                 TO   OUT-ACCT-ID.
254:           MOVE   ACCT-ID         TO   ARR-ACCT-ID.
277:           MOVE   ACCT-ID            TO VB1-ACCT-ID
278:                                        VB2-ACCT-ID.
```

Bob's SPEC found none of `OUT-ACCT-ID`, `ARR-ACCT-ID`, `VB1-ACCT-ID`, or
`VB2-ACCT-ID` — all four, in one file, missed. Line 277-278 is a single
COBOL sentence moving one value into *two* receiving fields; Bob missed both
halves of it, not just the second one — this isn't a "read only the first
target of a multi-target MOVE" bug specifically, it's that this file's
local fan-out logic doesn't appear to have been traced at all. `CBACT01C.cbl`
already had a hit on the literal `ACCT-ID` token elsewhere (it's one of the
15 originally-FIELD-AWARE programs), which may be exactly why SPEC didn't
look further inside it for more — it had already "found the field" by name
and moved on, rather than continuing to trace where that value goes next
within the same file.

## The other 16 misses, categorized

Every miss fits one of a small number of program-local roles — this is a
short list of *kinds* of gap, not 20 unrelated surprises:

- **Before/after image work fields for update validation** (`COACTUPC.cbl`):
  `ACUP-OLD-ACCT-ID`/`-X`, `ACUP-NEW-ACCT-ID`/`-X` — the account-update
  screen's mechanism for detecting whether a value changed. 4 misses, one
  program.
- **VSAM alternate-index key staging fields** (multiple programs):
  `WS-CARD-RID-ACCT-ID`/`-X`, `PA-ACCT-ID`, `CARD-UPDATE-ACCT-ID` — local
  work fields built specifically to drive a keyed file READ. 4+ misses.
- **File-record (FD SECTION) fields**: `FD-ACCT-ID`, `FD-XREF-ACCT-ID`,
  `FD-TRANCAT-ACCT-ID` — the physical record layout for a `SELECT`ed file,
  distinct from the WORKING-STORAGE copybook record. 3 misses. (`FD-ACCT-ID`
  in `CBACT01C.cbl` specifically is the one alias in this whole set that
  isn't fed by a literal MOVE at all — it arrives via a whole-record
  `READ ... INTO ACCOUNT-RECORD`, the 2026-08-29 rule extension; see
  `CHANGELOG.md`.)
- **Print/report/HTML rendering fields**: `ST-ACCT-ID` (statement print
  line, `CBSTM03A.CBL`). 1 miss.
- **Generic local working-storage copies**: `WS-ACCT-ID`, `WS-ACCT-ID-N`
  (`COACCT01.cbl`, `COPAUS0C.cbl`, `COTRN02C.cbl`). 2 misses.
- **Screen-pagination bookmarks**: `WS-CA-FIRST-CARD-ACCT-ID`,
  `WS-CA-LAST-CARD-ACCT-ID` (`COCRDLIC.cbl`, tracking the first/last card
  shown on the current results page). 2 misses.
- **Output-format fan-out** (the `CBACT01C.cbl` case above): `OUT-ACCT-ID`,
  `ARR-ACCT-ID`, `VB1-ACCT-ID`, `VB2-ACCT-ID`. 4 misses.

Every category above is "a program declared its own copy of this value for
a program-local purpose." None is "a genuinely ambiguous or hard-to-read
COBOL construct" — the MOVE statements themselves are plain, single-line,
unremarkable. The gap isn't reading difficulty; it's search scope.

## This is a floor, not a ceiling

The true alias count is stated as "at least 28," not "28," deliberately.
During this verification, one more likely alias surfaced incidentally and
was **not** added to the scored set: `COACTUPC.cbl:3960`,
`MOVE ACUP-NEW-ACCT-ID TO ACCT-UPDATE-ID` — a ninth locally-declared
receiving field, found only because it happened to sit on the next line
after a field already being checked for an unrelated reason. It was never
searched for systematically (its name doesn't contain `ACCT-ID` as a
substring, so it fell outside the method used to build the original
candidate list), so it isn't included in the 28 or in Bob's recall
denominator. Its existence is reported here as evidence that 28 is a floor:
a codebase this size likely contains more local aliases than any
substring-based search, including the one this ground truth started from,
will surface. The precision claim (8/8) is unaffected by this — it concerns
only what Bob actually claimed. The recall claim (28.6%) should be read as
an upper bound on how good the true recall could possibly look, not a
tight estimate.

## What this justifies about the product

This is the argument for the TRACE + VERIFY stages existing at all, not
just SPEC. A one-shot "resolve the field and its aliases" pass — what SPEC
did alone here — finds real, correct aliases and stops well short of the
full blast radius, with no visible signal that it stopped short. The
system this project builds doesn't stop at SPEC: TRACE independently
inspects every candidate program's own body for exactly this kind of local
MOVE chain, and VERIFY re-checks every claim regardless of which stage
produced it. This document is the evidence for why that two-stage design
is load-bearing, not decorative — **with one correction, below**: as
originally written, TRACE and VERIFY's own instructions would not have
closed this gap either.

## Postscript, 2026-08-29: the gap was partly instructed, not purely emergent

The measurement above was taken by running SPEC alone. When
`bob-package/.bob/agents/program-tracer.md` and `hit-verifier.md` were
reviewed afterward, both turned out to encode the *same* mistake this
document just measured: `program-tracer.md` instructed subagents that any
identifier not an exact match to the given target/alias list should be
recorded as a `near_miss_signal`, full stop — no check for whether it was
genuinely fed by the target's value. `hit-verifier.md`'s Step 4 was the
same shape: a longer or different token was an automatic **REJECT**,
labeled "substring of a different identifier," with no alias check at
all. `reference/tiers.md`'s "Near-miss signals" section defined near miss
the same way. Under the ground truth's own alias rule
(`docs/ground_truth/CHANGELOG.md`), that's wrong for the same reason the
old ground-truth classification was wrong before 2026-08-29's
reclassification: it treats "different token" as sufficient grounds for
rejection, when the actual test is whether the target's value flows into
that token.

This means the 28.6% recall figure measured above is not purely a
property of how well an LLM reasons about COBOL under good instructions —
a real share of it is a direct, mechanical consequence of the instructions
themselves telling TRACE to discard exactly the kind of finding this
document says it should have made. `FD-ACCT-ID`, `WS-ACCT-ID-N`,
`ACUP-OLD-ACCT-ID`, and the rest of the 20 misses were not just hard for
a one-shot SPEC pass to find — they were things a full TRACE run, as
originally instructed, would have found and then been told to throw away.

**This is the more useful finding of the two.** A model reasoning
imperfectly about ambiguous COBOL is a capability limit you work around
with better verification. A persona prompt that enforces the wrong rule
by construction is a design bug, and design bugs are fixable outright —
which is what happened: `program-tracer.md` now actively chases MOVE/
REDEFINES/record-level-READ-INTO chains from any confirmed field to
discover further local aliases, and both it and `hit-verifier.md` apply
the same alias-vs-near-miss test the ground truth itself uses before
calling anything a near miss. `reference/tiers.md` carries the shared
rule text so all three stages (and SYNTHESIS) can't drift out of sync
with it again. Full diffs: the `program-tracer`, `hit-verifier`, and
`tiers.md` files themselves, in this same commit.

**This fix has since been re-measured** — see "Current headline" at the
top of this document and the full detail in
[`docs/ACCURACY.md`](ACCURACY.md): 100% program recall, 100% tier
accuracy, 100% alias recall against the documented ground truth plus 7
additional real aliases found beyond it. The expectation stated above
("recall improves by construction") held, by a wider margin than
expected — but that same measurement also found a real, remaining gap
(near-miss coverage on one identifier family, 9/14 not 14/14), reported
in full in `ACCURACY.md` rather than left out now that the headline
number is good. A persona-prompt bug being fixable outright, and staying
honest about what the fix did and didn't fully close, are both part of
the same finding.
