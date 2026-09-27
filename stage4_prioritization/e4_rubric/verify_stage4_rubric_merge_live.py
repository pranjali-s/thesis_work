"""
Independent verification of the live-rerun Stage 4 rubric merge.
Does NOT trust stage4_scores_merged_live.json's own output -- re-derives
keys and value ranges directly from the two source inputs
(stage4_input_items_live.json, rubric_judgment_scores.py's JUDGMENT dict).
"""
import json
from rubric_judgment_scores import JUDGMENT

with open("stage3_input" if False else "stage4_input_items_live.json") as f:
    source_items = json.load(f)
with open("stage4_scores_merged_live.json") as f:
    merged = json.load(f)

errors = []

# 1. Key set equality: merged keys == Stage 3's 77 roadmap-item keys
source_keys = {(it["category"], it["cluster_id"]) for it in source_items}
merged_keys = {(r["category"], r["cluster_id"]) for r in merged}
if source_keys != merged_keys:
    errors.append(f"Key mismatch: {source_keys ^ merged_keys}")
else:
    print(f"1. Key set equality: PASSED ({len(source_keys)} keys match exactly)")

# 2. No duplicate keys in merged output
if len(merged) != len(merged_keys):
    errors.append(f"Duplicate keys in merged output: {len(merged)} rows, {len(merged_keys)} unique keys")
else:
    print(f"2. No duplicates: PASSED ({len(merged)} rows, {len(merged_keys)} unique keys)")

# 3. Every merged row's actionability/overall_priority/justification matches JUDGMENT exactly
mismatches = 0
for r in merged:
    key = (r["category"], r["cluster_id"])
    exp_action, exp_overall, exp_just = JUDGMENT[key]
    if r["actionability"] != exp_action or r["overall_priority"] != exp_overall or r["justification"] != exp_just:
        mismatches += 1
        errors.append(f"Field mismatch at {key}")
print(f"3. Field-value fidelity vs. JUDGMENT source: {mismatches} mismatches / {len(merged)} rows")

# 4. All 7 scored dimensions (reach, severity, engagement, recency,
#    cross_platform_generality, actionability, overall_priority) are
#    integers in [1, 10] -- 0 out-of-scale values expected
DIMS = ["reach", "severity", "engagement", "recency", "cross_platform_generality",
        "actionability", "overall_priority"]
out_of_scale = 0
total_checked = 0
for r in merged:
    for d in DIMS:
        total_checked += 1
        v = r[d]
        if not isinstance(v, int) or not (1 <= v <= 10):
            out_of_scale += 1
            errors.append(f"Out-of-scale {d}={v} at {(r['category'], r['cluster_id'])}")
print(f"4. Scale check: {out_of_scale} out-of-scale values / {total_checked} values checked "
      f"({len(merged)} clusters x {len(DIMS)} dimensions)")

if errors:
    print(f"\nFAILED -- {len(errors)} error(s):")
    for e in errors[:20]:
        print(" -", e)
else:
    print("\nALL CHECKS PASSED.")
