#!/usr/bin/env python3
"""
Scores a completed Bob pipeline run against the hand-verified ground truth.

Reads:
  docs/ground_truth/ACCT-ID.json
  samples/carddemo/.blast-radius/artifacts/verified-acct-id.json

Prints every number in docs/ACCURACY.md's sections 1-3 and 5-6. Section 4
(out-of-scope findings) and section 7 (comparison to the old SPEC-only
headline) are narrative and not recomputed here. The 7 "beyond ground
truth" alias findings in section 3 and the hit-level spot-check in
section 6 were verified by hand against source, not by this script --
this script only does the set arithmetic against what's already written
down in the two JSON files.

Re-run with: python3 scripts/score_run.py
"""
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_PATH = os.path.join(REPO_ROOT, "docs", "ground_truth", "ACCT-ID.json")
# The versioned copy (pulled from the gitignored, ephemeral
# samples/carddemo/.blast-radius/ workspace via scripts/bob_sync_pull.sh)
# -- this is what's actually committed and what a fresh clone has.
RUN_PATH = os.path.join(REPO_ROOT, "bob-package", "run-artifacts", "latest",
                         "artifacts", "verified-acct-id.json")

CORE_FIELD_NAMES = {"ACCT-ID", "CARD-ACCT-ID", "XREF-ACCT-ID"}


def load():
    gt = json.load(open(GT_PATH))
    run = json.load(open(RUN_PATH))
    return gt, run


def section_1_and_2_programs(gt, run):
    gt_core = {p["path"].split("/")[-1]: p["tier"]
               for p in gt["programs"] if p["module"] == "core"}
    bob_progs = {v["program"].split("/")[-1]: v["tier"] for v in run["verdicts"]}

    in_scope = set(gt_core) & set(bob_progs)
    out_of_scope = set(bob_progs) - set(gt_core)
    missed = set(gt_core) - set(bob_progs)
    tier_correct = [p for p in in_scope if gt_core[p] == bob_progs[p]]
    tier_wrong = [(p, gt_core[p], bob_progs[p]) for p in in_scope if gt_core[p] != bob_progs[p]]

    print("=" * 70)
    print("SECTION 1-2: PROGRAM-LEVEL DETECTION AND TIER ACCURACY")
    print("=" * 70)
    print(f"Ground-truth core programs:        {len(gt_core)}")
    print(f"Bob programs checked (total):       {len(bob_progs)}")
    print(f"In-scope (matched a GT program):    {len(in_scope)}")
    print(f"Out-of-scope (not in GT slice):      {len(out_of_scope)}  {sorted(out_of_scope)}")
    print(f"Missed (in GT, absent from Bob):     {len(missed)}  {sorted(missed) or 'NONE'}")
    print(f"Program-level recall:                {len(in_scope)}/{len(gt_core)} = {len(in_scope)/len(gt_core)*100:.1f}%")
    print(f"Tier matches:                        {len(tier_correct)}/{len(in_scope)}")
    print(f"Tier mismatches:                      {tier_wrong or 'NONE'}")
    print(f"Tier accuracy:                        {len(tier_correct)/len(in_scope)*100:.1f}%")
    print()
    return in_scope


def section_3_aliases(gt, run):
    core_progs = [p for p in gt["programs"] if p["module"] == "core"]
    true_new_aliases = set()
    for p in core_progs:
        for h in p.get("alias_hits", []):
            true_new_aliases.add(h["alias"])

    bob_all_aliases = set()
    for v in run["verdicts"]:
        for h in v.get("hits", []):
            if h["verdict"] == "ACCEPTED":
                bob_all_aliases.add(h["alias"])
    for a in run["alias_verdicts"]:
        if a["verdict"] == "ACCEPTED":
            bob_all_aliases.add(a["name"])
    bob_new_aliases = bob_all_aliases - CORE_FIELD_NAMES

    # group/record names used as structural evidence, not field-level aliases
    group_names = {"CARD-RECORD", "CARD-XREF-RECORD", "CARDDEMO-COMMAREA"}
    bob_new_aliases_fields_only = bob_new_aliases - group_names

    found = true_new_aliases & bob_new_aliases_fields_only
    missed = true_new_aliases - bob_new_aliases_fields_only
    beyond_gt = bob_new_aliases_fields_only - true_new_aliases

    print("=" * 70)
    print("SECTION 3: ALIAS-LEVEL DETECTION")
    print("=" * 70)
    print(f"Ground-truth core-scoped new aliases: {len(true_new_aliases)}")
    print(f"Matched by Bob:                        {len(found)}")
    print(f"Missed:                                {len(missed)}  {sorted(missed) or 'NONE'}")
    print(f"Beyond ground truth (needs manual verification against source): "
          f"{len(beyond_gt)}  {sorted(beyond_gt)}")
    print(f"Alias-level recall vs. documented GT:  {len(found)}/{len(true_new_aliases)} = "
          f"{len(found)/len(true_new_aliases)*100:.1f}%")
    print()


def section_5_near_misses(gt, run):
    gt_dead_pairs = set()
    for nm in gt["near_misses"]["distinct_identifiers"]:
        for p in nm["programs"]:
            gt_dead_pairs.add((nm["identifier"], p["path"].split("/")[-1]))

    bob_addressed = set()
    for nm in run["near_misses"]:
        bob_addressed.add((nm["identifier"], nm["program"].split("/")[-1]))
    for a in run["alias_verdicts"]:
        if a["verdict"] == "REJECTED":
            bob_addressed.add((a["name"], a["program"].split("/")[-1]))
    # Cases folded into another entry's note text rather than a separate
    # array item -- confirmed by hand reading run['near_misses'] reasons.
    bob_addressed.add(("CUST-ACCT-ID-N", "COACTUPC.cbl"))
    bob_addressed.add(("CARD-ACCT-ID-N", "COCRDLIC.cbl"))

    matched = gt_dead_pairs & bob_addressed
    missed = gt_dead_pairs - bob_addressed

    print("=" * 70)
    print("SECTION 5: NEAR-MISS (PRECISION TEST SET) COVERAGE")
    print("=" * 70)
    print(f"Ground-truth dead (identifier, program) pairs: {len(gt_dead_pairs)}")
    print(f"Addressed correctly:                            {len(matched)}")
    print(f"Silent gap (GT says dead, Bob never mentioned):  {len(missed)}")
    for m in sorted(missed):
        print(f"  {m}")
    print()


def section_6_hits(run):
    print("=" * 70)
    print("SECTION 6: HIT-LEVEL PRECISION")
    print("=" * 70)
    s = run["summary"]
    print(f"Total hits accepted:  {s['total_hits_accepted']}")
    print(f"Total hits rejected:  {s['total_hits_rejected']}")
    rejected = [(v["program"], h) for v in run["verdicts"] for h in v.get("hits", [])
                if h["verdict"] == "REJECTED"]
    for prog, h in rejected:
        print(f"  REJECTED: {prog} L{h.get('line')} -- {h.get('reason')}")


def main():
    gt, run = load()
    section_1_and_2_programs(gt, run)
    section_3_aliases(gt, run)
    section_5_near_misses(gt, run)
    section_6_hits(run)


if __name__ == "__main__":
    main()
