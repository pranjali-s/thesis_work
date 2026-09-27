"""
Independent re-derivation of E4's live-rerun results. Does NOT import or
trust compute_e4_live.py or its stored e4_results_live.json -- re-reads the
three raw source files directly and recomputes the pairwise Spearman
correlation and the ground-truth-undefined finding from scratch.
"""
import csv
import json
from scipy.stats import spearmanr

with open("stage4_scores_merged_live.json", encoding="utf-8") as f:
    rubric = {(c["category"], c["cluster_id"]): c["overall_priority"] for c in json.load(f)}
with open("/home/claude/BL1_live/bl1_ranking.csv", encoding="utf-8") as f:
    bl1 = {(r["category"], r["cluster_id"]): float(r["bl1_cluster_score"]) for r in csv.DictReader(f)}
with open("/home/claude/E1_live/e2_final.json", encoding="utf-8") as f:
    e2 = {(r["category"], r["cluster_id"]): int(r["e2_matched"]) for r in json.load(f)}

keys = sorted(rubric.keys())
assert set(keys) == set(bl1.keys()) == set(e2.keys())
n_pos = sum(e2.values())

rho, p = spearmanr([rubric[k] for k in keys], [bl1[k] for k in keys])

with open("e4_results_live.json", encoding="utf-8") as f:
    stored = json.load(f)

errors = []
if stored["n_clusters"] != len(keys):
    errors.append(f"n_clusters mismatch: stored={stored['n_clusters']} recomputed={len(keys)}")
if stored["n_positive_e2"] != n_pos:
    errors.append(f"n_positive_e2 mismatch: stored={stored['n_positive_e2']} recomputed={n_pos}")
stored_rho = stored["pairwise_correlations"]["rubric_vs_bl1"]["rho"]
if abs(stored_rho - round(float(rho), 4)) > 1e-6:
    errors.append(f"rubric_vs_bl1 rho mismatch: stored={stored_rho} recomputed={round(float(rho),4)}")

print(f"Recomputed independently: n_clusters={len(keys)}, n_positive_e2={n_pos}, "
      f"rubric_vs_bl1 rho={rho:.4f} (p={p:.4g})")

if errors:
    print(f"\nFAILED -- {len(errors)} mismatch(es):")
    for e in errors:
        print(" -", e)
else:
    print("\nAll values matched exactly -- 0 mismatches. PASSED.")
