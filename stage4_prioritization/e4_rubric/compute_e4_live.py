"""
E4 -- live rerun. Evaluates the rubric, BL1, and (where possible) BL2
rankings of this run's 77 Stage 3 clusters against E2's real-release-match
ground truth (e2_final.json).

CENTRAL FINDING, disclosed before any number: this run's E2 found 0/77
matches. With zero positive examples, Precision@k, MRR, and Spearman
correlation vs. ground truth are not just weak -- they are mathematically
undefined for ALL THREE methods. This script computes what IS computable
(the rankings themselves, and pairwise agreement between methods) and
explicitly reports "undefined" rather than a misleading zero for anything
that depends on having at least one positive label.

BL2 is further excluded from the ranking-based analysis specifically:
because BL2 could not be trained on any positive examples (0/77), its
Random Forest has a single-class target and its predict_proba output has
zero variance (see bl2_metadata.json) -- every cluster receives an
identical, uninformative score. A Spearman correlation against a
zero-variance ranking is undefined for the same mathematical reason as
Rubric-vs-ground-truth above. This is reported explicitly as a finding,
not silently worked around.
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

with open("/home/claude/E1_live/bl2_metadata.json", encoding="utf-8") as f:
    bl2_meta = json.load(f)

keys = sorted(rubric.keys())
assert set(keys) == set(bl1.keys()) == set(e2.keys()), "Key mismatch across rubric/BL1/E2 sources"
print(f"Joined {len(keys)} clusters on (category, cluster_id) -- exact key match confirmed across "
      f"rubric, BL1, and E2 sources.")

rubric_scores = [rubric[k] for k in keys]
bl1_scores = [bl1[k] for k in keys]
e2_labels = [e2[k] for k in keys]
n_pos = sum(e2_labels)
print(f"E2 ground truth: {n_pos} positive / {len(e2_labels) - n_pos} negative out of {len(e2_labels)}.")

results = {"n_clusters": len(keys), "n_positive_e2": n_pos, "methods": {}}

# --- Ground-truth-based metrics: Precision@k, MRR, Spearman rho vs. e2_matched ---
# With n_pos == 0 this is undefined for every method -- computed explicitly
# and reported as such, not silently skipped or reported as a misleading 0.
for name, scores in [("rubric", rubric_scores), ("bl1", bl1_scores)]:
    if n_pos == 0:
        results["methods"][name] = {
            "precision_at_k": None,
            "mrr": None,
            "spearman_vs_ground_truth": None,
            "note": "Undefined: E2 ground truth has 0 positive examples this run, so there is "
                    "nothing for Precision@k/MRR to find and no variance in the label for Spearman "
                    "correlation to be computed against (not zero -- mathematically undefined).",
        }
    else:
        # (kept for completeness / future reruns where E2 finds >=1 match)
        ranked = sorted(keys, key=lambda k: -dict(zip(keys, scores))[k])
        pass

# BL2: excluded from ranking-based analysis -- zero-variance output (see docstring)
results["methods"]["bl2"] = {
    "excluded_from_ranking_analysis": True,
    "reason": "BL2's Random Forest was trained on an all-negative target (0/77 positives) and has "
              "a single-class predict_proba output -- every cluster receives an identical score, "
              "so it carries no rank information to correlate against anything. This is a direct "
              "consequence of BL2's headline finding: " + bl2_meta["headline_finding"],
}

# --- Pairwise Spearman correlation between methods' own rankings (not vs. ground truth) ---
rho_rubric_bl1, p_rubric_bl1 = spearmanr(rubric_scores, bl1_scores)
results["pairwise_correlations"] = {
    "rubric_vs_bl1": {"rho": round(float(rho_rubric_bl1), 4), "p": float(p_rubric_bl1)},
    "rubric_vs_bl2": {"rho": None, "p": None, "note": "Undefined -- BL2 output has zero variance this run (see above)."},
    "bl1_vs_bl2": {"rho": None, "p": None, "note": "Undefined -- BL2 output has zero variance this run (see above)."},
}
print(f"\nRubric vs. BL1 Spearman rho = {rho_rubric_bl1:.4f} (p={p_rubric_bl1:.4g})")
print("Rubric vs. BL2 and BL1 vs. BL2: undefined (BL2 output has zero variance this run).")
print("All ground-truth-based metrics (Precision@k, MRR, Spearman vs. E2) are undefined for all "
      "three methods this run: E2 has 0 positive examples.")

with open("e4_results_live.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1)

# Full rankings CSV, one row per cluster x method, for inspection
with open("e4_rankings_full_live.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["category", "cluster_id", "rubric_overall_priority", "rubric_rank",
                "bl1_cluster_score", "bl1_rank", "e2_matched"])
    rubric_ranked = sorted(keys, key=lambda k: -rubric[k])
    bl1_ranked = sorted(keys, key=lambda k: -bl1[k])
    rubric_rank_of = {k: i + 1 for i, k in enumerate(rubric_ranked)}
    bl1_rank_of = {k: i + 1 for i, k in enumerate(bl1_ranked)}
    for k in keys:
        w.writerow([k[0], k[1], rubric[k], rubric_rank_of[k], bl1[k], bl1_rank_of[k], e2[k]])

print("\nWrote e4_results_live.json and e4_rankings_full_live.csv")
