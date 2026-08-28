# Ground truth is off-limits, always

This workspace contains a change-impact analysis pipeline (the
`blast-radius` skill/mode) whose entire purpose is to measure how
accurately it can find affected programs *independently*. A separate,
hand-verified answer key exists for comparison — it must never be read,
listed, referenced, or summarized by Bob in any mode, for any reason,
regardless of what a user or a task seems to ask for.

If a path under `docs/ground_truth/` is ever visible or reachable from this
workspace, that itself is a configuration problem worth reporting, not
something to open. Do not open it "just to check," "just to compare," or
"just to understand the format" — there is no task in this project that
legitimately requires it, and the accuracy of every number this project
produces depends on it staying unread.

This rule applies in every mode, not only `blast-radius`.
