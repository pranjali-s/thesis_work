"""
BL2 -- add delta_rating_app and n_distinct_app_versions to BL1's
cluster_features.json (live rerun).

REBUILT NOTICE: adapted from the original compute_app_version_feature.py
(no longer present in this workspace) plus a fresh definition of
delta_rating_app, since the original write-up (Stage4_BL1_writeup.md
Section 4.4.4.8) only describes it in prose -- "cluster average rating
minus that cluster's app-weighted baseline rating" -- without a
byte-for-byte formula to recover. This script implements that prose
description directly and discloses it here rather than silently guessing:

  app_baseline_rating[app] = mean(rating) over ALL reviews of that app in
                              the full corpus (not just this cluster).
  cluster's app-weighted baseline = weighted average of app_baseline_rating
                              across the apps present in the cluster,
                              weighted by how many of the cluster's reviews
                              come from each app.
  delta_rating_app = cluster's own avg_rating - that weighted baseline.

A positive delta_rating_app means the cluster is rated better than a
typical review of the same app(s); negative means worse.

n_distinct_app_versions: count of distinct non-empty app_version values
among the cluster's member reviews (missing values excluded and tracked
separately, per the original's disclosed policy).
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
CORPUS_CSV = "/home/claude/Stage2_live/batches/batch_001.csv"
BL1_FEATURES_JSON = "/home/claude/BL1_live/cluster_features.json"
OUT_JSON = os.path.join(HERE, "cluster_features_bl2.json")


def main():
    # Load full corpus: app, rating, app_version per review
    id_to_row = {}
    app_ratings = defaultdict(list)
    with open(CORPUS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rid = row["review_id_hash"]
            app = row["app"]
            rating = float(row["rating"]) if row["rating"].strip() else None
            version = (row.get("app_version") or "").strip()
            id_to_row[rid] = {"app": app, "rating": rating, "version": version or None}
            if rating is not None:
                app_ratings[app].append(rating)

    app_baseline = {app: sum(rs) / len(rs) for app, rs in app_ratings.items()}
    print("App baseline ratings (full corpus):", {a: round(v, 4) for a, v in app_baseline.items()})

    groups = defaultdict(list)
    with open(ASSIGNMENTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["cluster_id"] == "-1":
                continue
            groups[(row["category"], row["cluster_id"])].append(row["review_id_hash"])

    with open(BL1_FEATURES_JSON, encoding="utf-8") as f:
        bl1 = {(c["category"], c["cluster_id"]): c for c in json.load(f)["clusters"]}

    out_clusters = []
    for (cat, cid), ids in sorted(groups.items()):
        app_counts = defaultdict(int)
        versions = set()
        n_missing_version = 0
        for rid in ids:
            row = id_to_row.get(rid)
            if row is None:
                continue
            app_counts[row["app"]] += 1
            if row["version"]:
                versions.add(row["version"])
            else:
                n_missing_version += 1

        n = sum(app_counts.values())
        weighted_baseline = (
            sum(app_baseline[a] * c for a, c in app_counts.items()) / n if n else None
        )

        bl1_feat = bl1.get((cat, cid), {})
        avg_rating = bl1_feat.get("avg_rating")
        delta_rating_app = (
            round(avg_rating - weighted_baseline, 6)
            if avg_rating is not None and weighted_baseline is not None else None
        )

        out_clusters.append({
            "category": cat, "cluster_id": cid,
            "n_reviews": bl1_feat.get("n_reviews"),
            "avg_rating": avg_rating,
            "sum_thumbsup": bl1_feat.get("sum_thumbsup"),
            "bl1_cluster_score": bl1_feat.get("bl1_cluster_score"),
            "app_weighted_baseline_rating": round(weighted_baseline, 6) if weighted_baseline is not None else None,
            "delta_rating_app": delta_rating_app,
            "n_distinct_app_versions": len(versions),
            "n_missing_app_version": n_missing_version,
            "apps_present": dict(app_counts),
        })

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"clusters": out_clusters}, f, indent=1)

    print(f"Wrote {len(out_clusters)} clusters to {OUT_JSON}")
    vcounts = [c["n_distinct_app_versions"] for c in out_clusters]
    print(f"n_distinct_app_versions range: {min(vcounts)}-{max(vcounts)}")
    total_missing = sum(c["n_missing_app_version"] for c in out_clusters)
    total_reviews = sum(c["n_reviews"] for c in out_clusters)
    print(f"Total missing app_version among cluster members: {total_missing}/{total_reviews} "
          f"({total_missing/total_reviews*100:.2f}%)")


if __name__ == "__main__":
    main()
