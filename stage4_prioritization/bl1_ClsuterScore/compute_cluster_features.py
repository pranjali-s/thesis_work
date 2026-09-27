"""
BL1 -- compute the ClusterScore ranking baseline.

LIVE RUN (this session): adapted from BL1_redo/compute_cluster_features.py
(itself a disclosed reconstruction matching the spec in Stage4_BL1_writeup.md
Section 4.4.4, since the original script no longer existed in any reachable
workspace -- see that file's header). This copy points at this session's own
live Stage 2 rerun output (Stage2_live/), not the original run's 65-cluster
output, and is executed for real against real data rather than a synthetic
smoke test.

Reproduces the cluster-ranking formula (ClusterScore) from:
  Wei, Courbis, Lambolais, Xu, Bernard & Dray, "Zero-shot Bilingual App
  Reviews Mining with Large Language Models", arXiv:2311.03058, 2023.

  ClusterScore = (w_rev * |reviews| + w_th * |thumbsup|) / (w_ra * rating)
  Published default weights: w_rev=1, w_th=0.1, w_ra=1 (used unmodified).

Inputs:
  ASSIGNMENTS_CSV  This session's live Stage 2 rerun output:
                   Stage2_live/clusters/cluster_assignments.csv
                   (cluster_id == "-1" rows are noise and are excluded)
  CORPUS_CSV       Stage2_live/batches/batch_001.csv -- the same full review
                   corpus (with rating, thumbs_up_count) used for this
                   session's live Stage 2 rerun.

Outputs:
  cluster_features.json   full per-cluster feature output
  bl1_ranking.csv          the ranking alone, sorted descending by score
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
CORPUS_CSV = "/home/claude/Stage2_live/batches/batch_001.csv"
OUT_DIR = HERE

W_REV = 1.0
W_TH = 0.1
W_RA = 1.0


def load_corpus(path):
    """Load review_id_hash -> {rating: float|None, thumbsup: int, thumbsup_imputed: bool}."""
    id_to_row = {}
    n_rating_missing = 0
    n_thumbsup_missing = 0
    n_total = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_total += 1
            rid = row["review_id_hash"]

            rating_raw = (row.get("rating") or "").strip()
            if rating_raw == "":
                rating = None
                n_rating_missing += 1
            else:
                rating = float(rating_raw)

            thumbsup_raw = (row.get("thumbs_up_count") or "").strip()
            if thumbsup_raw == "":
                thumbsup = 0
                thumbsup_imputed = True
                n_thumbsup_missing += 1
            else:
                thumbsup = int(float(thumbsup_raw))
                thumbsup_imputed = False

            id_to_row[rid] = {
                "rating": rating,
                "thumbsup": thumbsup,
                "thumbsup_imputed": thumbsup_imputed,
            }

    if n_total:
        print(f"Corpus loaded: {n_total} rows from {path}")
        print(f"  rating empty: {n_rating_missing} ({n_rating_missing / n_total * 100:.2f}%)"
              + ("  -- WARNING: BL1's original design assumes rating is always present; "
                 "these reviews will be excluded from avg_rating for any cluster they belong to."
                 if n_rating_missing else ""))
        print(f"  thumbs_up_count empty in source file: {n_thumbsup_missing} "
              f"({n_thumbsup_missing / n_total * 100:.2f}%)  -- imputed as 0, per disclosed policy")
    return id_to_row


def load_cluster_assignments(path):
    """Load (category, cluster_id) -> [review_id_hash, ...], excluding noise (-1)."""
    groups = defaultdict(list)
    n_noise = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["cluster_id"] == "-1":
                n_noise += 1
                continue
            groups[(row["category"], row["cluster_id"])].append(row["review_id_hash"])
    print(f"Cluster assignments loaded: {len(groups)} non-noise clusters "
          f"({n_noise} noise rows excluded).")
    return groups


def main():
    id_to_row = load_corpus(CORPUS_CSV)
    groups = load_cluster_assignments(ASSIGNMENTS_CSV)

    clusters = []
    total_thumbsup_imputed = 0
    total_reviews = 0
    total_missing_text = 0

    for (cat, cid), ids in sorted(groups.items()):
        n_reviews = len(ids)
        ratings = []
        sum_thumbsup = 0
        n_thumbsup_imputed = 0
        missing_text = 0

        for rid in ids:
            row = id_to_row.get(rid)
            if row is None:
                missing_text += 1
                continue
            if row["rating"] is not None:
                ratings.append(row["rating"])
            sum_thumbsup += row["thumbsup"]
            if row["thumbsup_imputed"]:
                n_thumbsup_imputed += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else None
        mean_thumbsup = sum_thumbsup / n_reviews if n_reviews else 0.0

        bl1_score = None
        if avg_rating and avg_rating > 0:
            bl1_score = (W_REV * n_reviews + W_TH * sum_thumbsup) / (W_RA * avg_rating)

        clusters.append({
            "category": cat,
            "cluster_id": cid,
            "n_reviews": n_reviews,
            "avg_rating": round(avg_rating, 6) if avg_rating is not None else None,
            "sum_thumbsup": sum_thumbsup,
            "mean_thumbsup": round(mean_thumbsup, 4),
            "n_thumbsup_imputed": n_thumbsup_imputed,
            "missing_text": missing_text,
            "bl1_cluster_score": round(bl1_score, 6) if bl1_score is not None else None,
        })

        total_thumbsup_imputed += n_thumbsup_imputed
        total_reviews += n_reviews
        total_missing_text += missing_text

    with open(os.path.join(OUT_DIR, "cluster_features.json"), "w", encoding="utf-8") as f:
        json.dump({"clusters": clusters}, f, indent=1)

    ranked = sorted(
        [c for c in clusters if c["bl1_cluster_score"] is not None],
        key=lambda c: c["bl1_cluster_score"], reverse=True,
    )
    with open(os.path.join(OUT_DIR, "bl1_ranking.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "rank", "category", "cluster_id", "bl1_cluster_score",
            "n_reviews", "avg_rating", "sum_thumbsup"])
        w.writeheader()
        for i, c in enumerate(ranked, start=1):
            w.writerow({
                "rank": i, "category": c["category"], "cluster_id": c["cluster_id"],
                "bl1_cluster_score": c["bl1_cluster_score"], "n_reviews": c["n_reviews"],
                "avg_rating": c["avg_rating"], "sum_thumbsup": c["sum_thumbsup"],
            })

    skipped = len(clusters) - len(ranked)
    print(f"\nWrote {len(clusters)} clusters to cluster_features.json")
    print(f"Wrote {len(ranked)} ranked clusters to bl1_ranking.csv"
          + (f" ({skipped} skipped -- avg_rating missing/zero)" if skipped else ""))
    print(f"Total reviews across all clusters: {total_reviews}")
    print(f"Total missing_text (assignment row with no corpus match): {total_missing_text}")
    if total_reviews:
        print(f"Total thumbs-up imputed: {total_thumbsup_imputed} "
              f"({total_thumbsup_imputed / total_reviews * 100:.2f}% of cluster-member reviews)")


if __name__ == "__main__":
    main()
