# Sample data scope: CardDemo, account/customer maintenance slice

## What's in the repo

`samples/carddemo/` is the full `app/` tree from
[aws-samples/aws-mainframe-modernization-carddemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo)
(Apache 2.0), cloned in full: 39 `.cbl`, ~62 `.cpy` (incl. case variants), 46
`.jcl`, 21 `.bms`, ~49,500 LOC across the core and optional (IMS/DB2/MQ)
modules.

The **inventory stage** of the analyzer runs against this entire tree, so the
demo shows realistic scale for a legacy estate (tens of thousands of LOC,
hundreds of copybook references) rather than a toy.

## Why a scoped ground-truth slice

Hand-verifying a field trace across the full ~130-file, 49.5k-LOC app is not
feasible in the time available before the hackathon deadline (2026-08-30). To
have a trustworthy answer key to compare the analyzer's output against, the
**ground truth is scoped to one vertical slice**: every program that `COPY`s
`CVACT01Y` (account record), `CVACT02Y` (card record), or `CVACT03Y` (card
cross-reference record).

This slice was chosen, not the alternative CBSA sample, because CardDemo is
the AWS-maintained reference application for mainframe-modernization tooling
demos specifically — same rationale, applied to CardDemo instead of CBSA
after a scoping correction.

## The slice, by the numbers

- **21 programs** COPY one of CVACT01Y/02Y/03Y with an active (non-commented)
  `COPY` statement. 17 are in the core `cbl/` app; 4 are in optional
  integration modules (`app-authorization-ims-db2-mq/`: 2,
  `app-transaction-type-db2/`: 1, `app-vsam-mq/`: 1) that demonstrate
  alternate IMS/DB2/MQ integrations of the same account/card domain.
  (Corrected from an earlier report of "20 programs, 16 core" — that was an
  arithmetic error in the summary prose; the underlying enumerated list was
  always complete. Re-verified 2026-08-28 by re-running the unique-file count
  independently; see `scripts/ground_truth_extract.py`'s `PROGRAMS` list for
  the authoritative 21-entry set.)
- This is slightly above the 8-20 program range targeted for hand
  verification within about an hour. No slice reduction was made, but if
  verification runs long, the 4 optional-module programs are the first
  candidates to drop (they're alternate integration demos, not part of the
  core online/batch path).
- Real dependency structure confirmed, not assumed: `COPY` statements were
  checked column-by-column (COBOL indicator column 7) to exclude 4 lines
  that are commented out in the source (`COCRDSLC.cbl`, `COCRDUPC.cbl` each
  have 2 dead `COPY` references to CVACT01Y/03Y that a naive text search
  would over-count).
- 3 of the 21 programs (`CBACT03C.cbl`, `COTRTLIC.cbl`, `CBACT02C.cbl`) COPY
  a slice copybook but never name an individual field from it in their own
  code — they only move/read/display the record as an opaque group item.
  They still matter structurally (a field-width change shifts the record
  layout under them) but they are not "field-aware" callers, which is a
  real distinction the impact scorecard should capture, not something to
  paper over as identical to programs that read the field's value.
- Some programs `COPY` a slice copybook that turns out to be entirely dead:
  no field from it, and no whole-group I/O on it, appears anywhere else in
  the file (`COTRN02C.cbl`/CVACT01Y, `COTRTLIC.cbl`/CVACT02Y). These are
  documented as UNCERTAIN in the ground truth files rather than force-fit
  into either tier — see `docs/ground_truth/`.

## Method

Every claim above was produced by grep/awk against the actual files, not
recalled from prior knowledge of CardDemo. The exact commands are captured in
[`scripts/survey_slice.sh`](../scripts/survey_slice.sh) — re-run it with
`bash scripts/survey_slice.sh` to reproduce the program list, descriptions,
and field usage counts.

## Target fields: final selection and exhaustive ground truth

Two of the three surveyed candidates were selected for exhaustive,
line-level, hand-verified ground truth (the medium candidate,
`ACCT-ACTIVE-STATUS`/`CARD-ACTIVE-STATUS`, was dropped as time-boxed — same
naming-trap lesson as the narrow field):

1. **Narrow — `ACCT-ADDR-ZIP`** (CVACT01Y, `PIC X(10)`). Scope: only the 14
   of 21 slice programs that actively COPY CVACT01Y (the only copybook that
   declares this field) — programs that never pull in CVACT01Y cannot be
   affected and are correctly absent from the ground truth, not listed as
   unaffected. Near miss: `CUST-ADDR-ZIP` (CVCUS01Y, a distinct declared
   customer-address field, also `PIC X(10)`), found via the same 21-program
   search — not assumed to exist, confirmed present in 6 programs including
   both narrow-field FIELD-AWARE programs.
2. **Wide — `ACCT-ID`** (CVACT01Y) / **`CARD-ACCT-ID`** (CVACT02Y) /
   **`XREF-ACCT-ID`** (CVACT03Y), all `PIC 9(11)`, confirmed as one logical
   value by `CBTRN01C.cbl:175` (`MOVE XREF-ACCT-ID TO ACCT-ID`) and
   `CBTRN01C.cbl:237` (`DISPLAY 'ACCOUNT ID : ' XREF-ACCT-ID`).

Full machine-readable ground truth: **`docs/ground_truth/ACCT-ID.json`** and
**`docs/ground_truth/ACCT-ADDR-ZIP.json`**. Each records, per affected
program: core/optional module, tier (FIELD-AWARE vs STRUCTURALLY-AFFECTED —
see each file's `tier_definitions`), every line hit with access kind and a
note, and (for STRUCTURALLY-AFFECTED programs) the group-level I/O evidence
that justifies the tier instead of the field name itself. Regenerate with
`python3 scripts/ground_truth_build.py`, which combines
`scripts/ground_truth_extract.py`'s deterministic tokenizing pass (COBOL
column-7-aware, string-literal-aware) with hand-verified classification data
embedded in the build script.

Tiers are **FIELD-AWARE**, **STRUCTURALLY-AFFECTED**, and **DEAD-COPY**
(promoted from an initial UNCERTAIN bucket to a full third tier: a program
that COPYs the copybook but never touches the resulting record at all — not
by field name, not even at group level — is real technical debt worth
surfacing, not an edge case to argue away).

**Wide field, as of 2026-08-28** (before the alias-rule reclassification —
see below): 15 FIELD-AWARE + 5 STRUCTURALLY-AFFECTED + 1 DEAD-COPY = 21 of
21 tiered. `COTRTLIC.cbl` COPYs CVACT02Y but never references
`CARD-RECORD` anywhere, with no group-level I/O either. One additional
dead-copy relationship is recorded as a *footnote* rather than a top-level
tier: `COTRN02C.cbl`'s COPY of CVACT01Y is dead, but the program's overall
wide-field tier stays FIELD-AWARE because it genuinely uses `XREF-ACCT-ID`
from a different copybook (CVACT03Y) — a program can be dead-copy on one
alias and field-aware on another. Near misses at that point: 31 distinct
locally-declared shadow/commarea variables (e.g. `CDEMO-ACCT-ID`,
`CC-ACCT-ID`, `WS-CARD-RID-ACCT-ID`) contain one of the three alias names
as a substring without being that field — 271 lines total that a naive
grep would misattribute (later corrected to 246 true unique lines; see
below).

**Updated 2026-08-29**: an alias rule was adopted — a field genuinely fed
by the target's value via an explicit MOVE (or a whole-record READ from a
record containing it) is an alias, not a near miss, because widening the
target requires widening it too. Applying it moved 217 of those 246 lines
(27 distinct identifiers) from near-miss to alias, and moved 3 programs
(`COACTVWC.cbl`, `COCRDSLC.cbl`, `COCRDUPC.cbl`) from STRUCTURALLY-AFFECTED
to FIELD-AWARE. Current wide-field tiers: **18 FIELD-AWARE + 2
STRUCTURALLY-AFFECTED + 1 DEAD-COPY = 21 of 21**. Current near-miss set (the
precision test set): **6 distinct identifiers, 23 lines** — genuinely dead
code, never fed by anything. Full rationale, the rule text, and what this
made possible: [`docs/ground_truth/CHANGELOG.md`](ground_truth/CHANGELOG.md)
and [`docs/FINDINGS.md`](FINDINGS.md).

**Narrow field**: 2 FIELD-AWARE + 11 STRUCTURALLY-AFFECTED + 1 DEAD-COPY =
14 of 14 tiered. `COTRN02C.cbl` is DEAD-COPY outright here (unlike the wide
field, it has no other copybook to be field-aware through for
ACCT-ADDR-ZIP specifically). Near miss `CUST-ADDR-ZIP`: 7 exact hits across
6 programs.

**Correction, 2026-08-28**: an earlier version of this document and the
initial survey report stated "20 programs, 16 core" for the slice. Re-
verification during ground-truth construction found the correct count is
**21 programs, 17 core** — the original enumerated table was actually
complete; only the summary arithmetic was wrong. See `git log` on this file
for the prior (incorrect) figure.
