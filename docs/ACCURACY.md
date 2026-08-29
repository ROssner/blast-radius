# Accuracy: the full pipeline, scored against ground truth

This scores a real end-to-end Bob run (SPEC → TRACE → VERIFY, SYNTHESIS
report generated from it) — not the SPEC-only measurement in the earlier
version of `docs/FINDINGS.md`. Raw transcript:
[`bob_sessions/blastradius_task02_full_pipeline.json`](../bob_sessions/blastradius_task02_full_pipeline.json).
Bob's own output: [`bob-package/run-artifacts/latest/artifacts/verified-acct-id.json`](../bob-package/run-artifacts/latest/artifacts/verified-acct-id.json)
(the file every number below is computed from) and the rest of that
directory — pulled via `scripts/bob_sync_pull.sh` from the ephemeral,
gitignored `samples/carddemo/.blast-radius/artifacts/` where Bob actually
wrote it, since that path doesn't survive a fresh clone. Report:
[`reports/impact-acct-id.html`](../reports/impact-acct-id.html).

**Headline: this run is dramatically better than the SPEC-only measurement,
and it is verified, not assumed.** Every number below either comes directly
from `verified-acct-id.json` or from me independently re-reading the cited
source lines myself — the method for each is stated so you can tell which
is which. The one real imperfection found (a partial gap in near-miss
coverage for one identifier family) is reported plainly, not smoothed over.

## Scope and rules applied (as instructed)

- **Core programs only.** Bob was instructed to exclude the 11
  optional-module programs it found relevant; those are out of scope for
  this run, not misses. Ground truth's optional-module programs (4, in
  `docs/ground_truth/ACCT-ID.json`) are excluded from both sides of every
  comparison below.
- **Programs outside the 21-program ground-truth slice are reported
  separately, not scored as false positives.** My ground truth was built
  by searching for `COPY CVACT01Y/02Y/03Y`; Bob's own alias-driven search
  legitimately found more candidate programs than that (e.g. any program
  touching the shared CICS commarea). I have no ground truth to check
  those against, so they're neither confirmed nor refuted — just listed.
- **UNCERTAIN entries are excluded from scoring entirely.** None were
  produced in this run (`verified-acct-id.json`'s `summary` reports zero
  `UNCERTAIN` verdicts) — everything Bob claimed got a definite ACCEPTED
  or REJECTED.
- **Tier assignment is scored separately from hit/alias detection**, per
  instruction — a program can be correctly *found* with the wrong *tier*,
  and that's a different kind of error than not finding it at all.

## 1. Program-level detection

Ground truth's 17 core programs vs. the 27 Bob actually assessed
(`verified-acct-id.json`'s 27 `verdicts` entries):

| | Count |
|---|---|
| Ground-truth core programs | 17 |
| Bob's programs, in-scope (matched a GT program) | 17 |
| Bob's programs, out-of-scope (not in GT's slice — see §4) | 10 |
| Ground-truth programs Bob missed entirely | **0** |

**Program-level recall: 17/17 = 100%.** **Program-level precision (of the
scorable set): 17/17 = 100%** — every in-scope claim matches a real
affected program; the 10 out-of-scope claims are reported in §4, not
counted against precision (per the scoring rule) or for it.

## 2. Tier accuracy (scored separately from detection)

Of the 17 correctly-found programs, comparing Bob's assigned tier to
ground truth's tier, name for name:

| Program | Ground truth | Bob | Match |
|---|---|---|---|
| CBACT01C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBACT02C.cbl | STRUCTURALLY-AFFECTED | STRUCTURALLY-AFFECTED | ✓ |
| CBACT03C.cbl | STRUCTURALLY-AFFECTED | STRUCTURALLY-AFFECTED | ✓ |
| CBACT04C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBEXPORT.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBIMPORT.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBSTM03A.CBL | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBTRN01C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBTRN02C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| CBTRN03C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COACTUPC.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COACTVWC.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COBIL00C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COCRDLIC.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COCRDSLC.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COCRDUPC.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |
| COTRN02C.cbl | FIELD-AWARE | FIELD-AWARE | ✓ |

**Tier accuracy: 17/17 = 100%.** This includes the three hardest cases in
the whole ground truth — `COACTVWC.cbl`, `COCRDSLC.cbl`, `COCRDUPC.cbl`,
the programs whose tier only changed from STRUCTURALLY-AFFECTED to
FIELD-AWARE in the 2026-08-29 reclassification because they use
`CDEMO-ACCT-ID`/`CC-ACCT-ID` rather than the literal target names. Bob
independently reached the same tier for all three, and for the same
reason: `COCRDUPC.cbl`'s hit list cites `CC-ACCT-ID` (COCRDUPC.cbl:752
and elsewhere) and `CDEMO-ACCT-ID` directly, not a group-level read.

One case worth naming specifically because it's the hardest one in the
whole exercise: `COTRN02C.cbl` has an active `COPY CVACT01Y` that's
genuinely dead (no `ACCT-ID`/`ACCOUNT-RECORD` reference anywhere), while
being genuinely FIELD-AWARE via `XREF-ACCT-ID` from a *different*
copybook. Ground truth records this as a footnote on an otherwise
FIELD-AWARE program. Bob's verifier reached the identical conclusion
independently, in its own words: *"CVACT01Y COPYed at line 89 but ACCT-ID
and ACCOUNT-RECORD never referenced in procedure division — dead copy for
ACCT-ID path only; XREF-ACCT-ID hits via CVACT03Y are valid."* This is not
a case Bob was told the answer to — it re-derived it.

## 3. Alias-level detection (the metric the old headline measured)

Ground truth's core-scoped set of confirmed aliases beyond the three
declared field names (`ACCT-ID`/`CARD-ACCT-ID`/`XREF-ACCT-ID`), pulled
from `docs/ground_truth/ACCT-ID.json`'s `alias_hits` on core-tiered
programs: **25 identifiers.** Every alias name Bob used anywhere in
`verified-acct-id.json` (pooling both `hits[].alias` and `alias_verdicts`,
ACCEPTED only, excluding the 3 declared names):

| | Count |
|---|---|
| Ground-truth core aliases | 25 |
| Matched by Bob | **25** |
| Missed | **0** |
| Beyond ground truth (Bob found, not in my documented set) | 7, independently verified below |
| Bob's own rejected alias claims | 1 (correct — see §5) |

**Alias-level recall against documented ground truth: 25/25 = 100%.**

### The 7 aliases Bob found beyond my documented ground truth

My ground truth is itself a floor, not a ceiling (stated explicitly in
the pre-existing `docs/FINDINGS.md`) — it was built by a substring search
for `ACCT-ID`-shaped names, which structurally cannot find an alias
spelled differently. Bob's active MOVE-chain tracing found several such
names. I did not take Bob's word for these — each was re-checked against
source directly, myself, just now:

| Identifier | Program | Verified evidence |
|---|---|---|
| `WS-LAST-ACCT-NUM` | CBACT04C.cbl | `CBACT04C.cbl:201`: `MOVE TRANCAT-ACCT-ID TO WS-LAST-ACCT-NUM` (TRANCAT-ACCT-ID is a confirmed alias) |
| `L11-ACCT` | CBSTM03A.CBL | `CBSTM03A.CBL:529`: `MOVE ACCT-ID TO L11-ACCT.` |
| `ACCT-UPDATE-ID` | COACTUPC.cbl | `COACTUPC.cbl:3960`: `MOVE ACUP-NEW-ACCT-ID TO ACCT-UPDATE-ID` — this is the exact identifier `docs/FINDINGS.md` already named as an example of the ground truth's own incompleteness, found independently by Bob here |
| `WS-ROW-ACCTNO` | COCRDLIC.cbl | `COCRDLIC.cbl:531/559/684`: fed from `CARD-ACCT-ID` earlier in the same paragraph, then read out at `MOVE WS-ROW-ACCTNO(1) TO ACCTNO1O OF CCRDLIAO` |
| `CCUP-OLD-ACCTID` | COCRDUPC.cbl | `COCRDUPC.cbl:671`: `MOVE CCUP-OLD-ACCTID TO CDEMO-ACCT-ID` |
| `CCUP-NEW-ACCTID` | COCRDUPC.cbl | `COCRDUPC.cbl:752`: `MOVE CC-ACCT-ID TO CDEMO-ACCT-ID CCUP-NEW-ACCTID` (multi-target MOVE) |
| `TRAN-REPORT-ACCOUNT-ID` | CBTRN03C.cbl | Already independently confirmed in the *original* hand-built ground truth's hit notes (`CBTRN03C.cbl:364`) — just never given its own alias-registry entry, since its spelling (`ACCOUNT-ID`, not `ACCT-ID`) fell outside the substring search that built the near-miss list |

All 7 check out. Zero false claims found among them.

*(Three more names — `CARD-RECORD`, `CARD-XREF-RECORD`, `CARDDEMO-COMMAREA`
— also appear as `alias` values in the raw output, but these are
whole-record/commarea group names used as STRUCTURALLY-AFFECTED and
PASSED-TO-PROGRAM evidence citations, not field-level alias claims. Not
errors, just a schema reuse worth flagging so they aren't miscounted as
either hits or misses in either direction.)*

## 4. Out-of-scope findings (not scored, reported as instructed)

10 of Bob's 27 checked programs fall outside my 21-program ground-truth
slice: `COADM01C.cbl`, `COMEN01C.cbl`, `CORPT00C.cbl`, `COSGN00C.cbl`,
`COTRN00C.cbl`, `COTRN01C.cbl`, `COUSR00C.cbl`, `COUSR01C.cbl`,
`COUSR02C.cbl`, `COUSR03C.cbl` — all tiered STRUCTURALLY-AFFECTED, each
via a single hit: they all `COPY COCOM01Y` and pass `CARDDEMO-COMMAREA`
through `EXEC CICS RETURN`/`XCTL COMMAREA(...)`. My ground truth was built
around `CVACT01Y`/`02Y`/`03Y` specifically and never evaluated whether
these 10 programs are genuinely affected — I have no basis to confirm or
refute the claims, so they're listed here, not scored. Spot-checked one
(`COADM01C.cbl:113`, `EXEC CICS RETURN ... COMMAREA (CARDDEMO-COMMAREA)`)
against source directly — the citation is accurate; whether that
constitutes "affected by an ACCT-ID change" the way this ground truth
defines the term is a scope question, not an accuracy one.

## 5. Near misses (the precision test set) — mostly right, one real gap

Ground truth's core-scoped dead-code near misses: 6 identifiers across 14
(identifier, program) pairs (`CARD-ACCT-ID-X`/`-N` in 3 programs each,
`CUST-ACCT-ID-X`/`-N` in 1 program, `WS-CARD-RID-ACCT-ID`/`-X` dead in 3
programs each). Checking every pair against what Bob's `near_misses` list
and rejected `alias_verdicts` actually addressed (including cases folded
into another entry's note rather than given a separate array item, e.g.
`CUST-ACCT-ID-N` mentioned inside the `CUST-ACCT-ID-X` entry):

| Pair addressed correctly | 9 / 14 |
|---|---|
| Silent gap (ground truth says dead, Bob never mentioned it at all) | **5 / 14** |

The 5 silent gaps are all `WS-CARD-RID-ACCT-ID` or its `-X` redefine, in
`COCRDLIC.cbl` and `COCRDUPC.cbl` (plus the `-X` redefine in
`COCRDSLC.cbl`, whose base field *was* correctly rejected). Bob's own
`hit-verifier` output does correctly reject `WS-CARD-RID-ACCT-ID` in
`COCRDSLC.cbl`, with reasoning that matches ground truth almost verbatim
(*"the only feeding MOVE (line 739) is commented out"*) — so the method
works when applied. It simply wasn't applied to this one identifier
family in two of the three programs where it needed to be. This is not a
false claim (Bob never asserted these were aliases) and not a wrong
rejection — it's an omission: `program-tracer`'s chain-following didn't
happen to walk into this specific dead end in every program it occurs in.
Worth fixing in the persona prompt (make the "also check every REDEFINES
sibling of anything you've confirmed dead" step as explicit as the
"chase every MOVE from anything you've confirmed alive" step already is),
but it is not scored as a false positive, since one was never made.

## 6. Hit-level precision (line-by-line claims within found programs)

From `verified-acct-id.json`'s own summary: **107 hits accepted, 2
rejected**, out of 109 total line-level claims TRACE made. Both
rejections were independently re-checked against source and are correct:
`CBACT02C.cbl:96` (`DISPLAY CARD-RECORD` — column 7 is `*`, confirmed
commented out) and the `COTRN02C.cbl` `ACCT-ID` claim discussed in §2
(confirmed genuinely dead for that specific path). Beyond the 2
rejections, I randomly sampled 6 of the 107 accepted hits, spanning 6
different programs and 5 different access kinds (`MOVE-SOURCE`, `READ`,
`PASSED-TO-PROGRAM`, `COMPARE`), and independently re-read every cited
line — all 6 matched exactly, including the access-kind classification.
This is a sample, not an exhaustive re-verification of all 107; the
sample found zero errors.

## 7. Comparing to the old SPEC-only headline — not a clean apples-to-apples number

The previous `docs/FINDINGS.md` headline was **8/28 ≈ 28.6%** alias
recall, measured from a SPEC-only run across the *full* 21-program slice
(core + optional). This run is core-only by instruction, so the honest
comparison is core-to-core: **25/25 = 100%** alias recall against the
core-scoped ground truth, plus 7 additional verified finds beyond it.
Both the scope (core vs. core+optional) and the pipeline stage measured
(SPEC alone vs. the full SPEC→TRACE→VERIFY pipeline with the corrected
personas) changed between these two measurements — this is not a
before/after of the identical thing, it's a comparison of what SPEC alone
finds vs. what the full pipeline finds, which is exactly the argument
`docs/FINDINGS.md` already made for why TRACE and VERIFY exist. This run
is the first actual evidence for that argument, not just its restatement.

## Reproducing this

`python3 scripts/score_run.py` reproduces every number in sections 1, 2,
3, 5, and 6 directly from `bob-package/run-artifacts/latest/artifacts/verified-acct-id.json`
against `docs/ground_truth/ACCT-ID.json`, filtered to `module == "core"`
on both sides. It does not re-verify the 7 "beyond ground truth" alias
findings in §3 or the hit-level spot-check sample in §6 against source —
those were checked by hand, by me, against the actual `.cbl` files, and
the script says so in its own docstring rather than silently implying
otherwise. Section 4 (out-of-scope findings) and section 7 (comparison to
the old headline) are narrative, not computed.
