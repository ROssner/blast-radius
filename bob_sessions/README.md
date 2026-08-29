# Bob task session exports

This directory holds raw IBM Bob IDE task session exports — the full
message/tool-call transcript of a Bob run, exported as JSON from Bob's own
task history. They exist as verifiable evidence for the claims made
elsewhere in this repo: what Bob actually did, not a paraphrase of it.

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
