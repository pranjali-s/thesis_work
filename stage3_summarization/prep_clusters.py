"""
Stage 3 -- data prep.

Joins Stage 2's cluster assignments with the original review text and
prepares one JSON file per non-noise cluster, ready for hierarchical LLM
summarization into a structured "roadmap item": title + 1-3 sentence
description + 2-3 verbatim supporting quotes.

Sampling policy (disclosed): clusters at or under SAMPLE_CAP reviews use
every review. Larger clusters draw a fixed-seed (42) random sample of
SAMPLE_CAP reviews rather than the full cluster.

Chunking policy: within whatever set of reviews is being summarized (all
of them, or the capped sample), reviews are split into chunks of
CHUNK_SIZE for hierarchical (map-then-reduce) summarization when the set
exceeds CHUNK_SIZE; smaller sets are summarized in one pass with no
chunking.

HARDCODED PATH NOTICE: STAGE2_DIR / BATCHES_DIR / ASSIGNMENTS_CSV below are
absolute, session-specific paths from the container that actually ran this
script. They will not exist on another machine -- edit them to point at your
own local copy of Stage 1's batch_*.csv files (BATCHES_DIR) and Stage 2's
cluster_assignments.csv (ASSIGNMENTS_CSV) before running this script.
"""
import csv
import glob
import json
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
# Hardcoded, session-specific -- see HARDCODED PATH NOTICE above.
STAGE2_DIR = "/home/claude/Stage2_live"
BATCHES_DIR = "/home/claude/Stage2_live/batches"
ASSIGNMENTS_CSV = os.path.join(STAGE2_DIR, "clusters", "cluster_assignments.csv")
PREP_DIR = os.path.join(HERE, "prep")

SAMPLE_CAP = 150
CHUNK_SIZE = 50
SEED = 42


def load_review_text():
    id_to_text = {}
    for fp in sorted(glob.glob(os.path.join(BATCHES_DIR, "batch_*.csv"))):
        with open(fp, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                id_to_text[row["review_id_hash"]] = {
                    "app": row["app"], "text": row["review_text"] or "",
                }
    return id_to_text


def main():
    os.makedirs(PREP_DIR, exist_ok=True)
    id_to_review = load_review_text()
    print(f"Loaded {len(id_to_review)} reviews with text.")

    groups = defaultdict(list)
    with open(ASSIGNMENTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["cluster_id"] == "-1":
                continue
            groups[(row["category"], row["cluster_id"])].append(row["review_id_hash"])

    print(f"{len(groups)} non-noise clusters found.")

    rng = random.Random(SEED)
    manifest = []
    for (cat, cid), ids in sorted(groups.items()):
        n_total = len(ids)
        if n_total > SAMPLE_CAP:
            sampled_ids = rng.sample(ids, SAMPLE_CAP)
            was_sampled = True
        else:
            sampled_ids = list(ids)
            was_sampled = False

        reviews = [{"id": rid, "app": id_to_review[rid]["app"], "text": id_to_review[rid]["text"]}
                   for rid in sampled_ids if rid in id_to_review]
        missing = len(sampled_ids) - len(reviews)

        chunks = [reviews[i:i + CHUNK_SIZE] for i in range(0, len(reviews), CHUNK_SIZE)]

        fname = f"{cat}__{cid}.json"
        out = {
            "category": cat, "cluster_id": cid,
            "n_total": n_total, "n_sampled": len(reviews),
            "was_sampled": was_sampled, "n_chunks": len(chunks),
            "chunks": chunks,
        }
        with open(os.path.join(PREP_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(out, f)

        manifest.append({
            "category": cat, "cluster_id": cid, "file": fname,
            "n_total": n_total, "n_sampled": len(reviews), "n_chunks": len(chunks),
            "missing_text": missing,
        })

    with open(os.path.join(HERE, "prep_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    total_missing = sum(m["missing_text"] for m in manifest)
    print(f"Wrote {len(manifest)} prep files to {PREP_DIR}/")
    print(f"Total reviews missing text (should be 0): {total_missing}")
    print(f"Clusters requiring sampling (>{SAMPLE_CAP}): {sum(1 for m in manifest if m['n_total']>SAMPLE_CAP)}")
    print(f"Clusters requiring chunking (>{CHUNK_SIZE} in sample): {sum(1 for m in manifest if m['n_chunks']>1)}")


if __name__ == "__main__":
    main()
