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

- **20 programs** COPY one of CVACT01Y/02Y/03Y with an active (non-commented)
  `COPY` statement. 16 are in the core `cbl/` app; 4 are in optional
  integration modules (`app-authorization-ims-db2-mq/`: 2,
  `app-transaction-type-db2/`: 1, `app-vsam-mq/`: 1) that demonstrate
  alternate IMS/DB2/MQ integrations of the same account/card domain.
- This sits at the top of the 8-20 program range targeted for hand
  verification within about an hour. No adjustment was made because 20 is
  within bounds, but if verification runs long, the 4 optional-module
  programs are the first candidates to drop (they're alternate integration
  demos, not part of the core online/batch path).
- Real dependency structure confirmed, not assumed: `COPY` statements were
  checked column-by-column (COBOL indicator column 7) to exclude 4 lines
  that are commented out in the source (`COCRDSLC.cbl`, `COCRDUPC.cbl` each
  have 2 dead `COPY` references to CVACT01Y/03Y that a naive text search
  would over-count).
- 3 of the 20 programs (`CBACT03C.cbl`, `COTRTLIC.cbl`, `CBACT02C.cbl`) COPY
  a slice copybook but never name an individual field from it in their own
  code — they only move/read/display the record as an opaque group item.
  They still matter structurally (a field-width change shifts the record
  layout under them) but they are not "field-aware" callers, which is a
  real distinction the impact scorecard should capture, not something to
  paper over as identical to programs that read the field's value.

## Method

Every claim above was produced by grep/awk against the actual files, not
recalled from prior knowledge of CardDemo. The exact commands are captured in
[`scripts/survey_slice.sh`](../scripts/survey_slice.sh) — re-run it with
`bash scripts/survey_slice.sh` to reproduce the program list, descriptions,
and field usage counts.

## Candidate target fields (surveyed, not yet exhaustively traced)

Three fields were surveyed as impact-analysis targets, chosen to vary in
blast radius and to include real naming aliases (the "account ID" vs
`ACCT-ID` problem naive grep can't resolve). Full writeup with evidence in
the handoff conversation; two of the three will be picked for an exhaustive
hand-verified trace next:

1. **Narrow** — `ACCT-ADDR-ZIP` (CVACT01Y), used in 2/20 programs
   (`CBEXPORT.cbl`, `CBIMPORT.cbl`). Alias trap: `CUST-ADDR-ZIP`
   (CVCUS01Y, outside the slice) is a *different* field co-resident in the
   same two programs — a "zip code" change request is ambiguous between the
   two without field-level resolution.
2. **Medium** — `ACCT-ACTIVE-STATUS` (CVACT01Y, 6/20) vs `CARD-ACTIVE-STATUS`
   (CVACT02Y, 5/20), union 9/20. Same suffix, same `PIC X(01)` shape, two
   distinct real-world fields (account status vs. card status).
3. **Wide** — `ACCT-ID` (CVACT01Y) / `CARD-ACCT-ID` (CVACT02Y) /
   `XREF-ACCT-ID` (CVACT03Y), union 17/20. Confirmed as one logical value
   under three names by `CBTRN01C.cbl:175` (`MOVE XREF-ACCT-ID TO ACCT-ID`)
   and `CBTRN01C.cbl:237` (`DISPLAY 'ACCOUNT ID : ' XREF-ACCT-ID` — the
   human-facing label "ACCOUNT ID" mapped directly onto the `XREF-ACCT-ID`
   code name).
