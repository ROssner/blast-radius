# Ground truth changelog

## 2026-08-29 — Alias rule adopted; `ACCT-ID` reclassified

### What changed

**Old rule** (through 2026-08-28): a hit only counted as the target field if
it was an *exact token match* to one of the three declared names (`ACCT-ID`,
`CARD-ACCT-ID`, `XREF-ACCT-ID`). Everything else — including working-storage
and commarea fields that plainly carried the same value under a different
name, like `CDEMO-ACCT-ID` — was bucketed as a "near miss," on the grounds
that it wasn't the declaration site.

**New rule**: a field is an **ALIAS** of the target if the target's value
flows into it via an explicit MOVE (either direction — both operands of a
MOVE must widen together or the narrower one truncates at runtime), or if it
REDEFINES a field that is itself alias-confirmed (same storage, so a MOVE
feeding one feeds both). A **2026-08-29 extension**: a field fed by a
whole-record `READ ... INTO` from a record containing the target also
counts — the truncation risk is identical, it just arrives via positional
record I/O instead of a field-level MOVE statement. A field stays a **NEAR
MISS** only if it is a genuinely different entity (different data, different
meaning), or if it's declared but demonstrably never fed by anything at all
(dead code — not a different entity, just no entity). A field whose feed is
*plausible but unprovable* from an explicit MOVE within the file being
checked is **EXCLUDED FROM SCORING** — neither a true positive nor a false
positive, rather than guessed either way.

The full rule text lives in `ACCT-ID.json`'s `definitions` block, not only
here — a judge reading the data file shouldn't have to find this changelog
first to know what "alias" means in it.

### Why it changed

The product's purpose is change-impact analysis: telling a developer
everything they need to touch before widening a field. **A developer
extending `ACCT-ID` must widen `CDEMO-ACCT-ID` too, or every value that
passes through the shared CICS commarea truncates at runtime the moment an
account number exceeds 11 digits.** Whether `CDEMO-ACCT-ID` is the
*declaration site* of the account number is irrelevant to that developer —
what matters is whether the value flows through it. The old rule optimized
for "is this literally the same name" when the product needs "does this need
to change too." That was the wrong question for this product's purpose, not
a wrong answer to the old question.

This was triggered by reviewing Bob's own SPEC-stage output
(`spec-acct-id.json`), which independently landed on the same insight —
it treated `CDEMO-ACCT-ID` and similar carriers as aliases, justified by
citing the exact MOVE bridges. The rule change was adopted and then applied
*independently*: every one of the resulting reclassifications was
re-verified against source directly, not copied from Bob's claims. Where
Bob's own 8 claimed aliases were checked, all 8 held up. Where Bob's method
(reading copybooks) systematically missed locally-declared aliases, this
reclassification did not repeat that gap — see `docs/FINDINGS.md` for the
full recall analysis this made possible.

### A bug fixed along the way, not part of the rule change

While rebuilding the near-miss list under the new rule, a double-counting
bug was found in the original extractor: a single physical line was counted
twice for the same identifier whenever that identifier contained **more
than one** of the three search targets as a substring (e.g.
`CARD-ACCT-ID-X` contains both `ACCT-ID` and `CARD-ACCT-ID`). This inflated
the previously-reported "271 near-miss lines" figure. Fixed in
`scripts/ground_truth_build.py` by deduplicating on `(token, path, line)`
before grouping. **The true, deduplicated pre-reclassification total was
246 lines, not 271.** This is a correctness fix to the counting mechanism,
independent of and prior to the rule change below — stated separately so
the two kinds of change (a bug fix vs. a policy change) aren't conflated in
anyone's later reading of this history.

### What moved (246 true lines, under the new rule)

| Bucket | Lines | Distinct identifiers |
|---|---|---|
| Reclassified NEAR MISS → ALIAS | **217** | 27 |
| Stays NEAR MISS (genuinely dead — declared, never fed, never read) | **23** | 6 |
| EXCLUDED FROM SCORING (plausible, unprovable) | **6** | 2 (`WS-CARD-RID-ACCT-ID` and its `-X` redefine, both only in `COACCT01.cbl`) |

**23 lines is the new precision test set** — a tool should find zero of
these. They are `CARD-ACCT-ID-X`/`-N` (dead in `COCRDLIC.cbl`,
`COCRDSLC.cbl`, `COCRDUPC.cbl` — declared, never referenced again) and
`CUST-ACCT-ID-X`/`-N` (dead in `COACTUPC.cbl`, same pattern), plus the dead
per-program portions of `WS-CARD-RID-ACCT-ID`/`-X` in the three programs
where their only candidate feed is a commented-out `MOVE` (column 7 = `*`).

### Tier changes this caused (not just a near-miss recount)

Three programs move from **STRUCTURALLY-AFFECTED** to **FIELD-AWARE**,
because they reference a now-confirmed alias directly by name, even though
they never name `ACCT-ID`/`CARD-ACCT-ID`/`XREF-ACCT-ID` themselves:

- `COACTVWC.cbl` — uses `CC-ACCT-ID` and `CDEMO-ACCT-ID` directly
- `COCRDSLC.cbl` — uses `CC-ACCT-ID`, `CDEMO-ACCT-ID`, `CC-ACCT-ID-N`
- `COCRDUPC.cbl` — uses `CC-ACCT-ID`, `CDEMO-ACCT-ID`, `CC-ACCT-ID-N`,
  `CARD-UPDATE-ACCT-ID`

Wide-field tier totals: **FIELD-AWARE 15 → 18, STRUCTURALLY-AFFECTED 5 → 2,
DEAD-COPY unchanged at 1** (still 21 of 21 accounted for). `COTRTLIC.cbl`
(the other former STRUCTURALLY-AFFECTED-adjacent case) does not move — it
was already confirmed to reference nothing at all, alias or otherwise.

### Methodology note: access-kind classification for the newly-added hits

The original 47 direct hits (the ones behind the 15 FIELD-AWARE programs
before this change) were each hand-classified line by line, with a
hand-written note. The 217 newly-reclassified alias lines are **not**
individually hand-annotated at that same depth — at this volume, doing so
inside the time available for this submission would trade correctness for
completeness. Instead, each is tagged with an automated pattern
classification (`scripts/ground_truth_build.py:classify_access_kind_auto`)
run against the exact `source_line` text already captured by the original
extractor, plus one hand-verified, quoted worked example per alias
identifier (see each alias's `evidence` field). Every line number is still
present and traceable to real source; the access-kind label on any
individual one of the 217 should be treated as a good-faith automated
classification, not a hand-verified one, and re-checked before being relied
on for something more consequential than this submission.

### Regenerating this file

`python3 scripts/ground_truth_build.py` — runs the original extraction and
hand-classification (`build_wide`), then applies this reclassification as
an explicit, separate transformation pass
(`apply_2026_08_29_reclassification`) over that output. The original,
pre-reclassification logic is untouched in the script; the reclassification
is additive and auditable as its own function, matching this changelog
entry line for line.
