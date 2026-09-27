"""
BL1 -- independent, from-scratch verification of bl1_cluster_score.

LIVE RUN (this session): adapted from BL1_redo/verify_bl1_independent.py,
pointed at this session's live Stage 2 rerun output. Per this project's
standing rule that a script's own printed output is not by itself
sufficient evidence, this file independently re-derives bl1_cluster_score
for every cluster DIRECTLY from the raw source files -- it does NOT import
compute_cluster_features.py and does NOT trust cluster_features.json's
stored intermediate values (it recomputes avg_rating from the raw
per-review ratings, not from a rounded stored field -- reusing a rounded
intermediate was an identified, disclosed pitfall in the original BL1
write-up, Section 4.4.4.9). It only reads cluster_features.json at the very
end, to compare its independently-computed score against what
compute_cluster_features.py stored, and reports the match/mismatch count.

Run compute_cluster_features.py first so cluster_features.json exists.
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
CORPUS_CSV = "/home/claude/Stage2_live/batches/batch_001.csv"
FEATURES_JSON = os.path.join(HERE, "cluster_features.json")

W_REV = 1.0
W_TH = 0.1
W_RA = 1.0
TOLERANCE = 1e-6


def main():
    # --- independently reload everything from the raw source files ---
    id_to_row = {}
    with open(CORPUS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rating_raw = (row.get("rating") or "").strip()
            thumbsup_raw = (row.get("thumbs_up_count") or "").strip()
            id_to_row[row["review_id_hash"]] = {
                "rating": float(rating_raw) if rating_raw else None,
                "thumbsup": int(float(thumbsup_raw)) if thumbsup_raw else 0,
            }

    groups = defaultdict(list)
    with open(ASSIGNMENTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["cluster_id"] == "-1":
                continue
            groups[(row["category"], row["cluster_id"])].append(row["review_id_hash"])

    recomputed = {}
    for (cat, cid), ids in groups.items():
        ratings = []
        sum_thumbsup = 0
        for rid in ids:
            row = id_to_row.get(rid)
            if row is None:
                continue
            if row["rating"] is not None:
                ratings.append(row["rating"])
            sum_thumbsup += row["thumbsup"]
        n_reviews = len(ids)
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        score = None
        if avg_rating and avg_rating > 0:
            score = (W_REV * n_reviews + W_TH * sum_thumbsup) / (W_RA * avg_rating)
        recomputed[(cat, cid)] = score

    # --- compare against the stored output ---
    with open(FEATURES_JSON, encoding="utf-8") as f:
        stored = json.load(f)["clusters"]

    n_checked = 0
    mismatches = []
    for c in stored:
        key = (c["category"], c["cluster_id"])
        stored_score = c["bl1_cluster_score"]
        indep_score = recomputed.get(key)
        n_checked += 1

        if stored_score is None and indep_score is None:
            continue
        if stored_score is None or indep_score is None:
            mismatches.append((key, stored_score, indep_score, "one is None"))
            continue
        if abs(stored_score - indep_score) > TOLERANCE:
            mismatches.append((key, stored_score, indep_score, "exceeds tolerance"))

    print(f"{n_checked} clusters checked.")
    print(f"Mismatches (tolerance {TOLERANCE}): {len(mismatches)}")
    for key, s, i, reason in mismatches[:20]:
        print(f"  {key}: stored={s} independent={i} ({reason})")

    print("\n" + ("PASSED" if not mismatches else "FAILED -- see discrepancies above"))


if __name__ == "__main__":
    main()
