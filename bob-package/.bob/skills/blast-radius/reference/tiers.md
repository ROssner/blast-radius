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

## Near-miss signals (not a tier — a precision-tracking category)

Any identifier that contains the target field name or an alias as a
substring without being an exact match to it (e.g. a locally-declared
working-storage or commarea field whose name was built from the real
field's name as a naming convention). These are never counted as hits.
They exist in the report only to demonstrate that the pipeline correctly
distinguished them from the real field — that distinction is the whole
point of this tool over a plain text search.
