# Blast Radius — Bob IDE package

This is the actual analysis engine for the Blast Radius project: a Bob
Skill, two subagent personas, and a custom mode, designed to run entirely
inside IBM Bob (2.0.3). Nothing here is a standalone script that calls an
LLM API outside of Bob — Bob's own agentic tool use (reading files, running
shell commands it writes itself, spawning subagents) *is* the pipeline.

## Layout

```
.bob/
  skills/blast-radius/
    SKILL.md              -- orchestrates all five pipeline stages
    reference/
      tiers.md             -- shared tier + access-kind vocabulary
      output-schema.md      -- exact JSON schema for every artifact, and the risk-score formula
      report-template.html  -- the final report's HTML/CSS shell; the skill fills in content only
  agents/
    program-tracer.md      -- TRACE persona: scans a small group of programs
    hit-verifier.md        -- VERIFY persona: independently re-checks every claimed hit
  rules/
    01-ground-truth-off-limits.md   -- hard instruction, all modes: never read docs/ground_truth/
  custom_modes.yaml         -- the "blast-radius" orchestrator mode
carddemo.bobignore          -- becomes samples/carddemo/.bobignore on push (keeps INVENTORY off binary sample data)
```

## Why the workspace is isolated

The ground truth this project's accuracy claim rests on lives at
`docs/ground_truth/` in the main repo. Three independent layers keep Bob
from ever seeing it:

1. **Isolated workspace root** (the real protection): you open
   `samples/carddemo/` in Bob, not the `blast-radius/` repo root.
   `docs/ground_truth/` is a sibling of `samples/`, not a descendant of
   `samples/carddemo/` — it is not merely hidden, it is outside the
   filesystem tree Bob can traverse from that root at all.
2. **`.bobignore`** at the `blast-radius/` repo root, in case anyone
   opens the parent folder instead. (IBM's own docs are explicit this
   isn't a hard sandbox — it's a second layer, not the primary one.)
3. **A rule file** (`.bob/rules/01-ground-truth-off-limits.md`) loaded in
   every mode, telling Bob explicitly never to read that path even if it
   somehow became reachable.

## How to run this

```
scripts/bob_sync_push.sh
```

This copies `.bob/` and `carddemo.bobignore` into `samples/carddemo/`
(the canonical copy stays here in `bob-package/` for version control and
for anyone reviewing the repo). Then:

1. Open `samples/carddemo/` as its own folder/workspace in Bob IDE — not
   the `blast-radius/` repo root.
2. Switch to the **Blast Radius** custom mode.
3. Describe your change request, e.g. *"I want to extend the account ID
   field — what's affected?"*
4. Bob loads the `blast-radius` skill and runs all five stages, spawning
   `program-tracer` subagents in small parallel groups and one
   `hit-verifier` at the end. See `SKILL.md` for the exact stage-by-stage
   design and the cost-discipline rules (grouped TRACE spawns, no
   conversation history passed to subagents, cached INVENTORY).
5. The report lands at
   `samples/carddemo/.blast-radius/reports/<field-slug>-impact-report.html`.

Then, to bring the output back into the main repo:

```
scripts/bob_sync_pull.sh
```

This copies the report into `reports/` and the intermediate artifacts into
`bob-package/run-artifacts/latest/`, so both are visible in this repo
without anyone needing to open the isolated workspace.

## Design notes for anyone reviewing this

- **TRACE runs in groups of 3-5 programs per subagent, not one-per-program
  and not one giant pass.** This was a deliberate coin-budget decision
  (40 Bobcoins total, no reruns to spare) — see `SKILL.md`'s "Cost
  discipline" section.
- **The personas are taught the METHOD, not handed a finished script.**
  `program-tracer.md` and `hit-verifier.md` explain COBOL column-7 comment
  rules, string-literal spans, and exact-token-vs-substring matching as
  *instructions*, and explicitly permit (and encourage) constructing small
  shell commands (`sed`, `awk`, `grep`) themselves as part of their
  reasoning. That's Bob using tools to do real analytical work, not a
  wrapper script Bob merely executes and reports on.
- **The report template is a fixed HTML/CSS shell with placeholder
  tokens** (`reference/report-template.html`), filled in by SYNTHESIS.
  This guarantees the final report's visual quality doesn't depend on how
  much design effort a given run happens to produce — the risk was too
  high with 40 coins and no room for a third attempt at making it look
  good.
