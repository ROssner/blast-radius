# Tier and access-kind vocabulary

Shared definitions used across SPEC, TRACE, VERIFY, and SYNTHESIS. Every
stage must use these exact tier names and access-kind names — do not
invent synonyms, so results merge cleanly without a translation step.

## Tiers (mutually exclusive, per program per field)

- **FIELD-AWARE** — the program's own code names the target field or one
  of its aliases as a complete, exact data-name token at least once,
  outside comments and outside string literals.
- **STRUCTURALLY-AFFECTED** — the program COPYs a copybook declaring the
  field/alias, and the copybook's record (01-level group) is referenced
  elsewhere as a whole (READ INTO, WRITE/REWRITE FROM, DISPLAY, or a CICS
  INTO()/FROM() clause), but the field itself is never named individually.
- **DEAD-COPY** — the program COPYs a copybook declaring the field/alias,
  but neither the field nor the record is referenced anywhere else in the
  file. Report this plainly: it's real technical debt the tool surfaces
  for free, not a failure to find something.
- **NOT-AFFECTED** — the program doesn't COPY a relevant copybook and has
  no reference to the field at all. Still worth recording explicitly for
  any program a TRACE group was asked to check, so gaps are visible.

Priority when a program relates to the field through more than one alias
with different outcomes (e.g. field-aware via one copybook, dead-copy via
another): the program's overall tier is the highest-priority tier it
achieves via ANY alias, in the order FIELD-AWARE > STRUCTURALLY-AFFECTED >
DEAD-COPY. Record the lower-tier alias relationship as a note rather than
dropping it — both facts matter to the report.

## Access kinds (per hit, FIELD-AWARE only)

- **READ** — the field is used as, or to compute, a file/record key
  (RECORD KEY IS, RIDFLD, KEYLENGTH, LENGTH OF used to size a keyed access).
- **WRITE** — the field is a target of a WRITE/REWRITE targeting the field
  itself (rare; usually field-level writes happen via MOVE, see below).
- **MOVE-SOURCE** — the field is the source operand of a MOVE (or a STRING
  building an output value from it).
- **MOVE-TARGET** — the field is the receiving operand of a MOVE.
- **DISPLAY** — the field is an operand of a DISPLAY statement.
- **COMPARE** — the field appears in an IF/WHEN/EVALUATE condition.
- **PASSED-TO-PROGRAM** — the field appears directly as an argument inside
  a CALL ... USING, EXEC CICS LINK, or EXEC CICS XCTL parameter list
  (commonly inside a COMMAREA(...) clause).

A single line can produce more than one hit (e.g. `MOVE X TO Y` where both
X and Y are aliases of the same target field — X is MOVE-SOURCE, Y is
MOVE-TARGET, on the same line).

## Alias discovery vs. near misses (get this wrong and recall collapses)

An identifier that does NOT exactly match the target field or an alias
you were given upfront is **not automatically a near miss**. The alias
list you're handed at the start of a trace is a starting point, not a
ceiling — programs routinely stage a copybook field's value into their
own locally-declared working-storage, commarea, or FD-section fields, and
those are aliases too, discoverable only by reading the program's own
body. Check every same-shaped identifier you encounter against the rule
below before classifying it either way. Getting this check backwards (or
skipping it) is the single biggest cause of under-reporting in this
pipeline — see `docs/FINDINGS.md` in the main repo for the measured
impact (a SPEC-only pass that stopped at copybook-declared names alone
found roughly 29% of the true aliases in a real run).

**ALIAS** — a same-shaped identifier carrying the target's value,
established by any of:

- **An explicit MOVE**, either direction, with the target (or an
  already-confirmed alias) as one operand — both operands must widen
  together or the narrower one truncates at runtime. *Example:*
  `CDEMO-ACCT-ID` (a CICS commarea field, copybook `COCOM01Y`) is an
  alias of `ACCT-ID`, confirmed by `COACTUPC.cbl:3805`:
  `MOVE ACCT-ID TO CDEMO-ACCT-ID`.
- **REDEFINES of a field that is itself alias-confirmed** — they share
  the same storage, so a MOVE feeding one feeds both; no separate MOVE
  into the redefining name is needed. *Example:* `ACUP-OLD-ACCT-ID-X`
  REDEFINES `ACUP-OLD-ACCT-ID`, which is alias-confirmed by
  `COACTUPC.cbl:3817`: `MOVE ACCT-ID TO ACUP-OLD-ACCT-ID`.
- **A whole-record READ ... INTO from a record containing the target
  field (or an alias)** — even with no field-level MOVE naming it, the
  two fields occupy the same physical record position and must be
  widened together or the read misaligns. *Example:* `FD-ACCT-ID` (the
  FD SECTION's own record field for `ACCTFILE-FILE`) is an alias of
  `ACCT-ID` in `CBACT01C.cbl`, established by
  `READ ACCTFILE-FILE INTO ACCOUNT-RECORD` — `ACCOUNT-RECORD` is the
  copybook record containing `ACCT-ID`.

Once confirmed (by you, during this trace, or given to you upfront), an
alias is a first-class name: hits against it use the same access-kind
vocabulary below, and a program whose only reference is to a confirmed
alias — never the originally-given target/alias names — is still
**FIELD-AWARE**, not STRUCTURALLY-AFFECTED and not a near miss.

**NEAR MISS** — the identifier is a genuinely different entity: different
real-world data, different meaning, no value ever flows from the target
into it, regardless of name similarity. *Example:* `CUST-EFT-ACCOUNT-ID`
(a customer's EFT bank-account number, copybook `CVCUS01Y`, `PIC X(10)`)
looks account-shaped but is never fed by `ACCT-ID` (`PIC 9(11)`) — it's a
different value with a different shape.

**NEAR MISS (dead)** — the identifier is declared but demonstrably never
fed by anything and never referenced again after its own declaration.
This is not "a different entity" — it holds no entity at all — but it's
still a near miss; say so as dead code specifically, since that's a real,
separate, reportable finding (technical debt), not the same thing as a
different-entity near miss. *Example:* `CARD-ACCT-ID-X`/`CARD-ACCT-ID-N`
(`COCRDLIC.cbl`, `COCRDSLC.cbl`, `COCRDUPC.cbl`) are declared inside a
`CICS-OUTPUT-EDIT-VARS` group and never referenced again anywhere in any
of the three files.

These are never counted as hits, in either sub-category. They exist in
the report to demonstrate the pipeline correctly distinguished them from
the real field — that precision is one half of this tool's value over a
plain text search. The other half is recall: finding every alias above,
not only the ones handed to you at the start.
