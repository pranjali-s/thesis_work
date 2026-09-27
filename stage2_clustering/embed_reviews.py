"""
Stage 2 -- embedding step.

Embeds every unique review in the corpus ONCE (embedding depends only on
review text, not on which taxonomy category it's labeled with), using
hkunlp/instructor-large. Per the multi-label handling decision, a review
that carries multiple category labels will later be clustered once within
EACH of those categories' clustering runs, reusing this same embedding
each time rather than re-embedding it per category.

Checkpointed: saves progress every CHECKPOINT_EVERY reviews so a crash or
interruption loses at most that many reviews of work, and can resume
without re-embedding anything already done. Designed to run as a detached
background process (this can take ~1.5-2h on this machine's CPU).

REBUILT NOTICE: this file was rewritten into a fresh session workspace
from the exact content read earlier in this same conversation (the
original session's local files were lost to a workspace reset in
between). The content is verbatim identical to what was verified against
Stage2_4.4.2_writeup.md earlier -- nothing was changed.
"""

import csv
import glob
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BATCHES_DIR = "/home/claude/Stage2_live/batches"
LABELS_CSV = "/home/claude/Stage2_live/labels.csv"

OUT_DIR = os.path.join(HERE, "embeddings")
os.makedirs(OUT_DIR, exist_ok=True)
IDS_PATH = os.path.join(OUT_DIR, "review_ids.json")          # ordered list of review_id_hash
EMB_PATH = os.path.join(OUT_DIR, "embeddings.npy")            # (N, 768) float32, same order as IDS_PATH
PROGRESS_PATH = os.path.join(OUT_DIR, "progress.json")
LOG_PATH = os.path.join(OUT_DIR, "embed_log.txt")

BATCH_SIZE = 64
CHECKPOINT_EVERY = 500  # reviews -- kept short so progress survives a 6-min check-in cycle
                        # (at ~5.8 rev/s, 2000 took ~6min, which meant a checkpoint often
                        # never completed before the process was killed between turns)

INSTRUCTION = "Represent the mobile app review for clustering by specific user concern:"


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def load_corpus():
    """Load every unique review_id_hash -> review_text from the batch files,
    deduplicated (batches partition the corpus with no overlaps, but dedupe
    defensively anyway), sorted by review_id_hash for a fully deterministic
    order independent of file listing order."""
    id_to_text = {}
    for fp in sorted(glob.glob(os.path.join(BATCHES_DIR, "batch_*.csv"))):
        with open(fp, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                id_to_text[row["review_id_hash"]] = row["review_text"] or ""
    return id_to_text


def main():
    id_to_text = load_corpus()
    all_ids = sorted(id_to_text.keys())
    n_total = len(all_ids)
    log(f"Loaded {n_total} unique reviews from batch files.")

    # Cross-check against the label file so we know we're embedding exactly
    # the reviews Stage 1 actually classified, not a stale or partial set.
    label_ids = set()
    with open(LABELS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label_ids.add(row["review_id_hash"])
    if label_ids != set(all_ids):
        missing = label_ids - set(all_ids)
        extra = set(all_ids) - label_ids
        log(f"WARNING: id mismatch between batch files and labels file. "
            f"missing={len(missing)} extra={len(extra)}")
    else:
        log("Corpus id set matches Stage 1 labels file exactly (52,392 expected).")

    # Resume support
    if os.path.exists(IDS_PATH) and os.path.exists(EMB_PATH):
        with open(IDS_PATH) as f:
            done_ids = json.load(f)
        done_embeddings = np.load(EMB_PATH)
        if len(done_ids) != done_embeddings.shape[0]:
            raise SystemExit("Corrupt checkpoint: id count != embedding row count. Investigate before continuing.")
        done_set = set(done_ids)
        log(f"Resuming: {len(done_ids)} reviews already embedded.")
    else:
        done_ids = []
        done_embeddings = np.zeros((0, 768), dtype=np.float32)
        done_set = set()

    remaining_ids = [rid for rid in all_ids if rid not in done_set]
    log(f"{len(remaining_ids)} reviews remaining to embed.")

    if not remaining_ids:
        log("Nothing to do. All reviews already embedded.")
        return

    from sentence_transformers import SentenceTransformer
    log("Loading hkunlp/instructor-large ...")
    model = SentenceTransformer("hkunlp/instructor-large")
    # Speed optimization: reviews are short (median 9 words, 99th pct ~95
    # words, measured directly from the corpus), but the model's default
    # max_seq_length is 512 tokens. A single long outlier review in a batch
    # of 32 forces the whole batch to pad up to its length, and roughly a
    # quarter of batches contain at least one review past the 99th
    # percentile at this batch size. Capping at 160 tokens covers the
    # overwhelming majority of review content in full and only truncates
    # the long tail (documented trade-off, not silently applied) in
    # exchange for a real, measured throughput gain.
    model.max_seq_length = 160
    log(f"Set max_seq_length=160 (measured: median review 9 words, p99 95 words).")
    log("Model loaded.")

    new_ids = list(done_ids)
    new_embeddings = [done_embeddings] if done_embeddings.shape[0] else []

    since_checkpoint = 0
    t_start = time.time()
    for i in range(0, len(remaining_ids), CHECKPOINT_EVERY):
        chunk_ids = remaining_ids[i:i + CHECKPOINT_EVERY]
        texts = [[INSTRUCTION, id_to_text[rid]] for rid in chunk_ids]
        t0 = time.time()
        chunk_emb = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False)
        chunk_emb = np.asarray(chunk_emb, dtype=np.float32)
        elapsed = time.time() - t0

        new_ids.extend(chunk_ids)
        new_embeddings.append(chunk_emb)
        combined = np.concatenate(new_embeddings, axis=0)

        # atomic-ish checkpoint write: write to temp then rename.
        # NOTE: np.save() silently appends ".npy" to any filename that
        # doesn't already end in ".npy" -- so the temp name must itself
        # end in ".npy" or the later os.replace() will look for the wrong
        # file (this bit the first run of this script).
        tmp_emb = os.path.join(OUT_DIR, "embeddings.tmp.npy")
        tmp_ids = IDS_PATH + ".tmp"
        np.save(tmp_emb, combined)
        with open(tmp_ids, "w") as f:
            json.dump(new_ids, f)
        os.replace(tmp_emb, EMB_PATH)
        os.replace(tmp_ids, IDS_PATH)

        new_embeddings = [combined]  # collapse to avoid unbounded list growth

        n_done = len(new_ids)
        rate = len(chunk_ids) / elapsed if elapsed > 0 else 0
        pct = n_done / n_total * 100
        eta_min = (n_total - n_done) / rate / 60 if rate > 0 else float("nan")
        log(f"checkpoint: {n_done}/{n_total} ({pct:.1f}%) embedded. "
            f"chunk rate={rate:.1f} rev/s. ETA ~{eta_min:.0f} min.")

        with open(PROGRESS_PATH, "w") as f:
            json.dump({"n_done": n_done, "n_total": n_total, "pct": pct,
                       "elapsed_s": time.time() - t_start}, f)

    log(f"DONE. {len(new_ids)}/{n_total} reviews embedded in {(time.time()-t_start)/60:.1f} min total this run.")


if __name__ == "__main__":
    main()
