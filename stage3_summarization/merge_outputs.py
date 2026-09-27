"""
Stage 3 -- merge the 6 parallel agents' per-group output files into one
master file, cross-checked against prep_manifest.json for completeness
(every (category, cluster_id) pair from Stage 2 present exactly once).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
GROUP_FILES = [f"group{i}.json" for i in range(1, 7)]

with open(os.path.join(HERE, "prep_manifest.json")) as f:
    manifest = {(m["category"], m["cluster_id"]): m for m in json.load(f)}

items = []
for fn in GROUP_FILES:
    with open(os.path.join(OUT_DIR, fn), encoding="utf-8") as f:
        group_items = json.load(f)
    for it in group_items:
        it["cluster_id"] = str(it["cluster_id"])  # normalize: some agents wrote int, manifest keys are str
        it["source_group_file"] = fn
        items.append(it)

print(f"Total items merged: {len(items)}")

# completeness check against Stage 2's actual clusters
seen = set()
dupes = []
for it in items:
    key = (it["category"], it["cluster_id"])
    if key in seen:
        dupes.append(key)
    seen.add(key)

missing = set(manifest.keys()) - seen
extra = seen - set(manifest.keys())
print(f"Duplicates: {len(dupes)} {dupes[:5]}")
print(f"Missing from output (in Stage 2 but not summarized): {len(missing)} {list(missing)[:5]}")
print(f"Extra in output (not a real Stage 2 cluster): {len(extra)} {list(extra)[:5]}")

# attach provenance from prep_manifest
for it in items:
    key = (it["category"], it["cluster_id"])
    m = manifest.get(key, {})
    it["n_total"] = m.get("n_total")
    it["n_sampled"] = m.get("n_sampled")
    it["n_chunks"] = m.get("n_chunks")
    it["was_sampled"] = m.get("n_total", 0) > m.get("n_sampled", 0)

items.sort(key=lambda it: (it["category"], it["cluster_id"]))

with open(os.path.join(HERE, "stage3_roadmap_items.json"), "w", encoding="utf-8") as f:
    json.dump(items, f, indent=1)

import csv
with open(os.path.join(HERE, "stage3_roadmap_items.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["category", "cluster_id", "n_total", "n_sampled", "was_sampled", "n_chunks",
                "title", "description", "quote1_review_id", "quote1", "quote2_review_id", "quote2",
                "quote3_review_id", "quote3"])
    for it in items:
        quotes = it.get("quotes", [])
        q = [(quotes[i]["review_id"], quotes[i]["quote"]) if i < len(quotes) else ("", "")
             for i in range(3)]
        w.writerow([it["category"], it["cluster_id"], it["n_total"], it["n_sampled"],
                    it["was_sampled"], it["n_chunks"], it["title"], it["description"],
                    q[0][0], q[0][1], q[1][0], q[1][1], q[2][0], q[2][1]])

print(f"\nWrote stage3_roadmap_items.json and .csv ({len(items)} rows).")
print("PASSED" if not dupes and not missing and not extra else "FAILED -- see discrepancies above")
