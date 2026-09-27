"""
Stage 3 -- merge the 6 parallel blind-rating agents' output files into one
master ratings file, cross-checked against stage3_roadmap_items.json for
completeness (every (category, cluster_id) item rated exactly once), then
compute aggregate + per-category stats and flag anything scoring <=2 on
any dimension.
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RATINGS_DIR = os.path.join(HERE, "ratings")
GROUP_FILES = [f"group{i}_ratings.json" for i in range(1, 7)]

with open(os.path.join(HERE, "stage3_roadmap_items.json"), encoding="utf-8") as f:
    roadmap_items = json.load(f)
roadmap_keys = {(it["category"], str(it["cluster_id"])) for it in roadmap_items}

ratings = []
for fn in GROUP_FILES:
    with open(os.path.join(RATINGS_DIR, fn), encoding="utf-8") as f:
        group_ratings = json.load(f)
    for r in group_ratings:
        r["cluster_id"] = str(r["cluster_id"])
        r["source_group_file"] = fn
        ratings.append(r)

print(f"Total ratings merged: {len(ratings)}")

seen = set()
dupes = []
for r in ratings:
    key = (r["category"], r["cluster_id"])
    if key in seen:
        dupes.append(key)
    seen.add(key)

missing = roadmap_keys - seen
extra = seen - roadmap_keys
print(f"Duplicates: {len(dupes)} {dupes[:5]}")
print(f"Missing (roadmap item never rated): {len(missing)} {list(missing)[:5]}")
print(f"Extra (rated but not a real roadmap item): {len(extra)} {list(extra)[:5]}")

completeness_ok = not dupes and not missing and not extra

ratings.sort(key=lambda r: (r["category"], r["cluster_id"]))
with open(os.path.join(HERE, "stage3_ratings.json"), "w", encoding="utf-8") as f:
    json.dump(ratings, f, indent=1)

# aggregate stats
def avg(xs):
    return round(sum(xs) / len(xs), 2) if xs else None

overall = {
    "n_items": len(ratings),
    "faithfulness_avg": avg([r["faithfulness"] for r in ratings]),
    "clarity_avg": avg([r["clarity"] for r in ratings]),
    "usefulness_avg": avg([r["usefulness"] for r in ratings]),
}

by_cat = defaultdict(list)
for r in ratings:
    by_cat[r["category"]].append(r)

per_category = {}
for cat, rs in sorted(by_cat.items()):
    per_category[cat] = {
        "n_items": len(rs),
        "faithfulness_avg": avg([r["faithfulness"] for r in rs]),
        "clarity_avg": avg([r["clarity"] for r in rs]),
        "usefulness_avg": avg([r["usefulness"] for r in rs]),
    }

flagged = [
    {
        "category": r["category"], "cluster_id": r["cluster_id"],
        "faithfulness": r["faithfulness"], "clarity": r["clarity"], "usefulness": r["usefulness"],
        "faithfulness_note": r.get("faithfulness_note", ""),
        "clarity_note": r.get("clarity_note", ""),
        "usefulness_note": r.get("usefulness_note", ""),
    }
    for r in ratings
    if r["faithfulness"] <= 2 or r["clarity"] <= 2 or r["usefulness"] <= 2
]

summary = {
    "completeness_check": {
        "duplicates": dupes, "missing": list(missing), "extra": list(extra), "passed": completeness_ok,
    },
    "overall": overall,
    "per_category": per_category,
    "flagged_le2_any_dimension": flagged,
}

with open(os.path.join(HERE, "stage3_ratings_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=1)

print(f"\nOverall: {overall}")
print(f"\nFlagged (<=2 on any dimension): {len(flagged)}")
for fl in flagged:
    print(f"  {fl['category']} / {fl['cluster_id']}  F={fl['faithfulness']} C={fl['clarity']} U={fl['usefulness']}")

print("\n" + ("PASSED -- completeness check clean." if completeness_ok else "FAILED -- see discrepancies above."))
