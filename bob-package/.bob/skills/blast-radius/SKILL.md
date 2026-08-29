---
name: blast-radius
description: Change-impact analysis for a legacy COBOL/RPG/CL codebase. Use when the user describes a change request against a field or file in this codebase (e.g. "extend the account number field", "add a status code to the order file") and wants to know every affected program, ranked by risk, before making the change. Runs a five-stage pipeline (INVENTORY, SPEC, TRACE, VERIFY, SYNTHESIS) and produces a single self-contained HTML report.
---

# Blast Radius: change-impact analysis

You are running a five-stage pipeline against the CardDemo COBOL
application that is the root of the current workspace. The user gives you
a plain-language change request naming a field or file. Your job is to
find every program that would need review before that change ships, tier
each one honestly, verify every claim against the real source, and produce
one polished HTML report. Read this whole file before starting stage 1.

**Hard rule, applies to every stage and every subagent you spawn: never
open, list, or read anything under `docs/ground_truth/`.** That path
should not even be visible from this workspace (see `.bobignore` and the
workspace root), but if you ever see it referenced or reachable, treat it
as off-limits and say so rather than opening it. This tool's entire value
is being independently correct — reading an answer key would make every
number in the final report meaningless.

Shared vocabulary for tiers and access kinds: `reference/tiers.md`.
Exact artifact file formats: `reference/output-schema.md`. Read both now.

All working output goes under `.blast-radius/` at the workspace root
(`artifacts/` for intermediate JSON, `reports/` for the final HTML). Never
write inside `app/` — you are analyzing that tree, not modifying it.

## Cost discipline (read this before spawning anything)

The user has a small, fixed budget for this. Follow these rules without
being asked again:

- **Cache INVENTORY.** If `.blast-radius/artifacts/inventory.json` already
  exists and looks complete, do not re-walk the repository — reuse it.
  Only redo INVENTORY if the user says the codebase changed or the file is
  missing/corrupt.
- **TRACE subagents work in groups of 3-5 programs, never one-per-program
  and never all-at-once.** Split the candidate program list from SPEC into
  groups of 3-5 and spawn one `program-tracer` subagent per group, all in
  the same turn so they run in parallel.
- **Never pass conversation history into a subagent spawn.** Each
  `program-tracer` or `hit-verifier` spawn gets a short, self-contained
  prompt built from the current stage's data only — the field/alias list,
  the specific file paths or claims it needs, the output path, and nothing
  else. Passing prior conversation turns multiplies token cost for no
  benefit here.
- **VERIFY is one subagent spawn, not one per TRACE group.** Merge all
  TRACE outputs first, then spawn a single `hit-verifier` with the full
  claim list.
- Before running the full pipeline on all candidate programs for the
  first time in a session, consider proposing a small dry run (one TRACE
  group of 3-5 programs, verified, previewed) to the user so a prompt bug
  is caught cheaply rather than after a full run.

## Stage 1 — INVENTORY

Scope: the entire CardDemo application (everything under `app/`), not just
programs related to any one field. This stage runs once and is reused
across every future field/change-request run in this session.

1. Walk the tree with your `command` tool (`find`, `grep`, `wc`). Classify
   files by extension: `.cbl`/`.CBL` (COBOL programs), `.cpy`/`.CPY`
   (copybooks), `.jcl`/`.JCL` (batch job control), `.bms` (CICS screen
   maps), plus whatever else you find. Note core (`app/cbl/`, `app/cpy/`,
   `app/jcl/`, `app/bms/`) vs. optional integration modules (any
   `app/app-*/` directory) as a `module` field per program — this
   distinction matters later for risk scoring.
2. For every copybook, record its name, path, and the 01-level record
   name(s) it declares (open the file, don't guess from the filename).
3. Build the COPY graph: for every program, every copybook it COPYs and
   the line number, **respecting COBOL column 7** — a COPY statement whose
   7th character is `*` or `/` is commented out and must be recorded as
   `"active": false`, not skipped and not counted as a real dependency.
4. Build a best-effort call graph: `EXEC CICS LINK`/`EXEC CICS XCTL`
   (note the `PROGRAM(...)` target) and `CALL '...' USING` statements.
   This doesn't need to be exhaustive for this stage to be useful — do not
   spend excessive tool calls chasing every dynamic call target.
5. Write `.blast-radius/artifacts/inventory.json` per
   `reference/output-schema.md`.

## Stage 2 — SPEC

Input: the user's plain-language change request, plus `inventory.json`'s
copybook list.

1. Read the copybooks that look relevant by content, not just filename —
   scan field declarations for names and comments that plausibly match
   the human phrase (e.g. "account number" is a paraphrase; a field named
   `ACCT-ID`, `ACCOUNT-NUM`, or similar in an account-shaped record is a
   candidate). Do not assume a single spelling; a real field can appear
   under multiple genuinely different data-names across sibling copybooks
   that describe the same real-world value (check for a MOVE bridging two
   differently-named fields as strong confirming evidence they're aliases
   of the same concept, and check for a DISPLAY whose literal label uses
   the human phrase next to the field, e.g. `DISPLAY 'ACCOUNT ID :' X`
   confirms `X` is what a person would call "account ID").
2. If the request is ambiguous between two clearly different fields (e.g.
   an account-level field vs. a customer-level field with a similar name
   and shape), do not silently pick one — surface both candidates to the
   user and ask, or proceed with the more literal reading and flag the
   other explicitly in the final report as a "did you mean" note. Do not
   silently guess when a real ambiguity exists; that's exactly the kind of
   mistake this tool exists to prevent.
3. From `inventory.json`'s COPY graph, build `candidate_programs`: every
   program with an **active** COPY of a copybook containing one of the
   resolved aliases. This is the list TRACE will split into groups.
4. Write `.blast-radius/artifacts/spec-<field-slug>.json` per
   `reference/output-schema.md`.

## Stage 3 — TRACE

Input: `spec-<field-slug>.json`'s `aliases` and `candidate_programs`.

**The alias list from SPEC is a starting point, not the ceiling for this
stage.** SPEC only resolves aliases declared in shared copybooks (that's
what reading copybooks can tell you); a large share of a real field's
aliases are declared locally inside individual programs' own
WORKING-STORAGE or FD SECTIONS, and those are only discoverable by reading
each program's own body. That is TRACE's job, not SPEC's — see
`docs/FINDINGS.md` in the main repo for a measured run where skipping this
step cut recall to roughly 29%. Concretely:

1. Split `candidate_programs` into groups of 3-5.
2. For each group, spawn a subagent using the **program-tracer** persona,
   in the same turn as every other group (parallel dispatch). Give each
   spawn only: the resolved field name and full alias list (with
   copybook/record/PIC info), that group's file paths, and the output
   path `.blast-radius/artifacts/trace-<field-slug>-group-<N>.json`. Do
   not include anything else. Each `program-tracer` persona is itself
   instructed to actively chase MOVE/REDEFINES/READ-INTO chains from any
   confirmed field to discover further, locally-declared aliases within
   its assigned files — you don't need to re-instruct this here, just
   don't strip it out of the spawn prompt.
3. Wait for all groups to complete, then read each group's output file,
   including its `newly_discovered_aliases` array — these are exactly the
   locally-declared aliases SPEC's copybook-only search couldn't find.

## Stage 4 — VERIFY

Input: every `trace-<field-slug>-group-*.json` file.

1. Merge all claimed hits (and structural/dead-copy evidence) from every
   group into one flat claim list, and separately merge every group's
   `newly_discovered_aliases` into one flat alias-claim list.
2. Spawn exactly one subagent using the **hit-verifier** persona, giving
   it the field/alias list, the full merged hit-claim list, the full
   merged alias-claim list, and the output path
   `.blast-radius/artifacts/verified-<field-slug>.json`. Do not spawn more
   than one verifier and do not split verification by group — the whole
   point is one independent pass over everything TRACE claimed.
3. Read the result. Build `final_programs` by keeping only ACCEPTED hits
   (with any `corrected_alias`/`corrected_access_kind`/`corrected_tier`
   applied) and dropping REJECTED ones. Fold every ACCEPTED entry from
   `alias_verdicts` into the alias list for the report exactly like any
   other confirmed alias — these are the aliases a copybook-only search
   would have missed, and the report should not distinguish them visually
   from ones SPEC found first. Anything UNCERTAIN goes in the report's
   methodology/notes section, not into the ranked table, with its reason
   preserved.

## Stage 5 — SYNTHESIS

Input: `verified-<field-slug>.json`.

1. Compute `risk_score` per program in `final_programs` using the exact
   formula in `reference/output-schema.md` — do not improvise a different
   scoring approach. Sort descending by risk score.
2. Build a Mermaid graph: the target field as a central node, each alias
   as a node connected to it, and every affected program connected to the
   alias(es) it uses, colored/shaped by tier (e.g. FIELD-AWARE programs
   filled solid, STRUCTURALLY-AFFECTED hatched/outlined, DEAD-COPY
   dashed/greyed). Keep it a `graph LR` or `graph TD` Mermaid flowchart;
   don't invent a diagram type the report template doesn't expect.
3. Read `reference/report-template.html`. Fill in every `{{PLACEHOLDER}}`
   token with real content:
   - `{{FIELD_NAME}}`, `{{FIELD_ALIAS_BADGES}}` (one `<span class="badge">`
     per alias), `{{CHANGE_REQUEST_TEXT}}`, `{{GENERATED_AT}}`,
     `{{SCOPE_SUMMARY}}` (e.g. file counts from inventory + candidate count
     from SPEC).
   - The five `{{STAT_*}}` tiles from your tier and near-miss counts.
   - `{{PROGRAM_TABLE_ROWS}}` — one `<tr>` per program in `final_programs`,
     following the existing table's column order; use the `tier-pill`
     classes (`field-aware` / `structural` / `dead-copy`) already defined
     in the template's CSS, and a `risk-bar-fill` span whose `width` is
     proportional to `risk_score` (pick colors from the CSS variables
     already defined — do not add new colors or restyle the page).
   - `{{MERMAID_DIAGRAM}}` — the raw Mermaid definition text from step 2.
   - `{{NEAR_MISS_TABLE_ROWS}}` and `{{REJECTION_REASON_BREAKDOWN}}` from
     hit-verifier's rejected verdicts and `summary.rejection_reasons`.
   - `{{STAT_NEAR_MISS_PROGRAM_COUNT}}` — count of distinct programs with
     at least one rejected near miss.
4. **Do not modify the template's CSS or overall structure** — it was
   designed to look right without further styling. Only fill content.
   This keeps the report's visual quality independent of how much
   creative effort this particular run puts into design.
5. Write the completed file to
   `.blast-radius/reports/<field-slug>-impact-report.html`.
6. Tell the user, in your own final message (not just the file), the
   headline numbers: total affected, tier breakdown, near misses rejected,
   and the report's file path.
