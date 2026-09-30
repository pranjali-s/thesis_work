"""
Stage 2 -- clustering step.

Runs UMAP -> HDBSCAN separately within each of the 17 taxonomy categories,
using the precomputed instructor-large embeddings from embed_reviews.py.

Per the multi-label handling decision: a review carrying multiple category
labels is clustered once within EACH category's run, reusing the same
base embedding each time (no re-embedding). This means the same
review_id_hash can appear in more than one output row (once per category
it's labeled with), by design.

HDBSCAN parameters are a first-pass default (min_cluster_size scaled to
each category's pool size, since categories range from 303 to 17,435
reviews and a single fixed value would either fragment the small
categories or under-cluster the large ones) and are explicitly flagged as
likely needing iteration once the results are inspected -- this is not
tuned against B6 yet, just a reasonable starting point.

REBUILT NOTICE: this file was rewritten into a fresh session workspace
from the exact content read earlier in this same conversation (the
original session's local files were lost to a workspace reset in
between). The content is verbatim identical to what was verified against
Stage2_4.4.2_writeup.md earlier -- nothing was changed, including the
CATEGORY_OVERRIDES values.

HARDCODED PATH NOTICE: LABELS_CSV below is hardcoded to the execution
environment this script was actually run in, not to a portable relative
path. It will not exist on another machine. Before reusing this script,
point LABELS_CSV at a review_id_hash/labels CSV (e.g.
stage1_classification/full_corpus_classifier/stage1_full_corpus_labels.csv).
This script also expects embed_reviews.py's embeddings/ output (IDS_PATH,
EMB_PATH below) to already exist in this same folder -- run embed_reviews.py
first if it doesn't.
"""

import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# EDIT THIS before running on a different machine -- see HARDCODED PATH
# NOTICE in the module docstring above.
LABELS_CSV = "/home/claude/Stage2_live/labels.csv"
EMB_DIR = os.path.join(HERE, "embeddings")
IDS_PATH = os.path.join(EMB_DIR, "review_ids.json")
EMB_PATH = os.path.join(EMB_DIR, "embeddings.npy")

OUT_DIR = os.path.join(HERE, "clusters")
os.makedirs(OUT_DIR, exist_ok=True)

UMAP_N_COMPONENTS = 5
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.0
UMAP_RANDOM_STATE = 42

MIN_CLUSTER_SIZE_FLOOR = 8
MIN_CLUSTER_SIZE_DIVISOR = 60  # pool_size // this, floored at MIN_CLUSTER_SIZE_FLOOR

# Per-category overrides. The default formula (min_cluster_size = n // 60)
# left four categories with high noise (most reviews unassigned to any
# cluster) or over-fragmentation for their size: TRADE_EXECUTION,
# PREDICTION_MARKETS, ACCOUNT_LIFECYCLE, ADVERTISING_NOTIFICATIONS. A
# parameter sweep (min_cluster_size x min_samples x cluster_selection_method)
# was run on each of these four categories individually, and the setting
# that minimized noise while keeping at least 3 clusters (i.e. not
# collapsing to a single trivial split) was selected for each. Applying a
# single global override (e.g. min_samples=5 for everyone) was tested and
# rejected: it improves some categories but measurably worsens others
# (e.g. CUSTOMER_SUPPORT going from 0% noise to ~5%), so tuning is scoped
# per-category. The other 13 categories keep the default formula, which
# already produced low noise (0-9%) results.
CATEGORY_OVERRIDES = {
    "TRADE_EXECUTION": {"min_cluster_size": 80, "min_samples": 3},
    "PREDICTION_MARKETS": {"min_cluster_size": 30, "min_samples": 5},
    "ACCOUNT_LIFECYCLE": {"min_cluster_size": 80, "min_samples": 10},
    "ADVERTISING_NOTIFICATIONS": {"min_cluster_size": 80, "min_samples": 3, "cluster_selection_method": "leaf"},
}


def log(msg):
    print(msg, flush=True)


def load_labels():
    id_to_labels = {}
    with open(LABELS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels = tuple(sorted(l.strip() for l in (row["labels"] or "").split("|") if l.strip()))
            id_to_labels[row["review_id_hash"]] = labels
    return id_to_labels


def main():
    with open(IDS_PATH) as f:
        review_ids = json.load(f)
    embeddings = np.load(EMB_PATH)
    assert len(review_ids) == embeddings.shape[0], "id/embedding count mismatch"
    id_to_idx = {rid: i for i, rid in enumerate(review_ids)}
    log(f"Loaded {len(review_ids)} embeddings, dim={embeddings.shape[1]}")

    id_to_labels = load_labels()
    all_cats = sorted(set(l for labels in id_to_labels.values() for l in labels))

    import umap
    from hdbscan import HDBSCAN

    summary_rows = []
    all_assignments = []  # review_id_hash, category, cluster_id, umap_x, umap_y (first 2 dims for reference)

    for cat in all_cats:
        cat_ids = [rid for rid, labels in id_to_labels.items() if cat in labels and rid in id_to_idx]
        n = len(cat_ids)
        idxs = [id_to_idx[rid] for rid in cat_ids]
        X = embeddings[idxs]

        min_cluster_size = max(MIN_CLUSTER_SIZE_FLOOR, n // MIN_CLUSTER_SIZE_DIVISOR)
        hdbscan_kwargs = {"min_cluster_size": min_cluster_size, "metric": "euclidean"}
        override_note = ""
        if cat in CATEGORY_OVERRIDES:
            hdbscan_kwargs.update(CATEGORY_OVERRIDES[cat])
            min_cluster_size = hdbscan_kwargs["min_cluster_size"]
            override_note = f" [override: {CATEGORY_OVERRIDES[cat]}]"

        log(f"\n=== {cat} (n={n}, min_cluster_size={min_cluster_size}){override_note} ===")

        reducer = umap.UMAP(
            n_components=UMAP_N_COMPONENTS,
            n_neighbors=min(UMAP_N_NEIGHBORS, max(2, n - 1)),
            min_dist=UMAP_MIN_DIST,
            random_state=UMAP_RANDOM_STATE,
            metric="cosine",
        )
        X_reduced = reducer.fit_transform(X)

        clusterer = HDBSCAN(**hdbscan_kwargs)
        cluster_labels = clusterer.fit_predict(X_reduced)

        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = int((cluster_labels == -1).sum())
        noise_pct = n_noise / n * 100 if n else 0

        log(f"  -> {n_clusters} clusters, {n_noise}/{n} noise ({noise_pct:.1f}%)")

        cluster_sizes = {}
        for lbl in cluster_labels:
            if lbl == -1:
                continue
            cluster_sizes[lbl] = cluster_sizes.get(lbl, 0) + 1
        if cluster_sizes:
            sizes_sorted = sorted(cluster_sizes.values(), reverse=True)
            log(f"  cluster sizes (largest first): {sizes_sorted}")

        summary_rows.append({
            "category": cat, "n_reviews": n, "min_cluster_size_param": min_cluster_size,
            "n_clusters": n_clusters, "n_noise": n_noise, "noise_pct": round(noise_pct, 1),
        })

        for rid, lbl, coord in zip(cat_ids, cluster_labels, X_reduced):
            all_assignments.append({
                "review_id_hash": rid, "category": cat, "cluster_id": int(lbl),
                "umap_dim0": float(coord[0]), "umap_dim1": float(coord[1]),
            })

    # write outputs
    with open(os.path.join(OUT_DIR, "cluster_assignments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["review_id_hash", "category", "cluster_id", "umap_dim0", "umap_dim1"])
        w.writeheader()
        w.writerows(all_assignments)

    with open(os.path.join(OUT_DIR, "cluster_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["category", "n_reviews", "min_cluster_size_param", "n_clusters", "n_noise", "noise_pct"])
        w.writeheader()
        w.writerows(summary_rows)

    log(f"\nWrote {len(all_assignments)} assignment rows and {len(summary_rows)} category summaries to {OUT_DIR}/")


if __name__ == "__main__":
    main()
