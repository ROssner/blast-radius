# Bob task session exports

This directory holds raw IBM Bob IDE task session exports — the full
message/tool-call transcript of a Bob run, exported as JSON from Bob's own
task history. They exist as verifiable evidence for the claims made
elsewhere in this repo: what Bob actually did, not a paraphrase of it.

### JSON vs. screenshots

The `.json` files are complete session exports from Bob IDE. The `.png`
files are screenshots of the session's consumption summary. Both formats
are included.

`blastradius_task01_inventory.png` is a screenshot of the `task01_inventory`
run (task title "Run the INVENTORY stage of the blast-radius skill only.
Stop after it...", cost 4.37), showing the COPY graph, call graph, and
notable-copybooks sections of Bob's INVENTORY output.

`blastradius_task02_full_pipeline_1.png` and `_2.png` are two screenshots
from the `task02_full_pipeline` run: the first shows the pipeline's final
chat summary as Bob wrote it, the second is a scroll further down the same
summary, showing the headline metrics table, top-5 risk-scored programs,
and the notable findings.

## `blastradius_task01_inventory.json`

A run of the Blast Radius skill's INVENTORY stage only (the task was
explicitly scoped: *"Run the INVENTORY stage... Do not run SPEC, TRACE,
VERIFY or SYNTHESIS. Do not spawn subagents."*), captured from the
`blast-radius` custom mode with the workspace opened on
`samples/carddemo/` per the design in [`bob-package/`](../bob-package/).

### Redaction: cosmetic, not substantive

Two values were removed before committing this file: the absolute
filesystem paths to two SKILL.md files —
`/home/rossner/.agents/skills/omarchy/SKILL.md` and
`/home/rossner/.claude/skills/waybar/SKILL.md` — both replaced with the
literal string `[REDACTED: unrelated personal skill path]`.

These two paths appear inside Bob's own system-prompt skill listing, which
enumerates every skill installed *globally* on the machine, not just this
project's. "Omarchy" and "Waybar" are Linux desktop-environment tools
completely unrelated to Blast Radius — their presence here is an artifact
of how Bob's environment happens to be configured on this machine, not
something relevant to this project or its accuracy claims. Nothing else in
the file was touched: this project's own paths
(`/home/rossner/blast-radius/samples/carddemo/...`), the exact command
history, the token/cost accounting, and the Bob-internal
`commandSecurityModel` detail are all left exactly as Bob produced them.
Weakening those would weaken the evidence value of this export; the two
redactions above don't, because they carry no information about this
project's behavior or accuracy.

### Ground-truth isolation: verifiable in this transcript

This is the concrete evidence behind the ground-truth protection claims in
the main [README](../README.md) and [`docs/SCOPE.md`](../docs/SCOPE.md).
The string `ground_truth` appears exactly **4 times** in this transcript.
All four are the *guardrail itself* being loaded into Bob's context —
never a tool call that opened, listed, or referenced the actual directory:

1. The `blast-radius` custom mode's `customInstructions`, loaded into the
   system prompt: *"Never read anything under docs/ground_truth/..."*
2. The full text of `.bob/rules/01-ground-truth-off-limits.md`, loaded as
   a workspace rule.
3. The continuation of that same rule file's body.
4. The hard-rule paragraph from `SKILL.md` itself, loaded when the skill
   activated: *"never open, list, or read anything under
   `docs/ground_truth/`."*

Zero occurrences are inside a tool-call block (`execute_command`,
`read_file`, or any file-listing result) — there is no point in this
transcript where Bob's tools touched that path. Combined with the
structural fact that `docs/ground_truth/` isn't even reachable from the
`samples/carddemo/` workspace root Bob was opened on (it's a sibling of
`samples/`, not a descendant of `samples/carddemo/`), this transcript is
direct, checkable evidence that the answer key stayed hidden from Bob
during this run — not just a design claim.

## `blastradius_task02_full_pipeline.json`

The real end-to-end run this project's accuracy claims are built on: SPEC
through SYNTHESIS against the change request *"extend the account
identifier field to support longer account numbers,"* core modules only
(the 11 optional-integration-module programs excluded by instruction),
producing `spec-acct-id.json`, 7 parallel `program-tracer` groups,
`verified-acct-id.json`, and the final report
(`samples/carddemo/.blast-radius/reports/impact-acct-id.html`). Every
number in [`docs/ACCURACY.md`](../docs/ACCURACY.md) traces back to
`verified-acct-id.json`, which this transcript is the source of.

### Redaction: identical treatment, same two paths

Same redaction as `task01`, nothing more: the same two absolute paths —
`/home/rossner/.agents/skills/omarchy/SKILL.md` and
`/home/rossner/.claude/skills/waybar/SKILL.md` — replaced with
`[REDACTED: unrelated personal skill path]`. They reappear here for the
same reason as before (Bob's system prompt re-lists every globally
installed skill on every task, not just this project's), and are removed
for the same reason: they describe this machine's personal setup, not
this project's behavior. Everything else — this project's own paths, the
full command history across all five stages and 7 TRACE subagent spawns,
token/cost accounting — is untouched.

### Ground-truth isolation: verified again, at much larger scale

The string `ground_truth` (or `ground-truth`) appears **27 times** in this
much longer transcript — expected, since the hard rule is loaded fresh
into every one of the 7 `program-tracer` spawns plus the single
`hit-verifier` spawn, on top of the system-prompt/mode/rule-file copies
counted in `task01`. Every one of the 27 is the guardrail text itself
(the custom mode's instructions, the rule file, SKILL.md's hard rule, and
each subagent persona's own hard-rule paragraph) being loaded into
context before that stage or subagent does any work. A pattern search for
anything resembling actual tool access to that path (a `read_file`
argument, an `execute_command` argument, a file-listing result naming it)
found zero matches. Across a run that spawned 8 separate subagents and
produced over 5MB of transcript, the isolation held completely — the
answer key was not read once.
