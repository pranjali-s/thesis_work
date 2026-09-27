"""
Final sanity check on stage1_full_corpus_labels.csv before treating Stage 1
as done. Run this after classify_reviews.py finishes.

Checks (same discipline as every other verification step in this project —
never trust a script's own printed summary):
  1. Real row count via proper CSV parsing (not naive line-counting).
  2. The set of review_id_hash in the output exactly matches the set in
     your corpus CSV (config.CORPUS_CSV) — no missing, no duplicate, no
     extra ids.
  3. Every row's labels are all from the valid 17-code vocabulary and
     non-empty.

Run:
    python3 verify_combined.py
"""

import csv
import config

def main():
    with open(config.CORPUS_CSV, newline="", encoding="utf-8") as f:
        corpus_ids = [r["review_id_hash"] for r in csv.DictReader(f)]
    corpus_id_set = set(corpus_ids)
    print(f"Corpus: {len(corpus_ids)} rows, {len(corpus_id_set)} unique review_id_hash")

    with open(config.COMBINED_OUTPUT_CSV, newline="", encoding="utf-8") as f:
        out_rows = list(csv.DictReader(f))
    out_ids = [r["review_id_hash"] for r in out_rows]
    out_id_set = set(out_ids)
    print(f"Combined output: {len(out_rows)} rows, {len(out_id_set)} unique review_id_hash")

    errors = []
    if len(out_ids) != len(out_id_set):
        errors.append(f"DUPLICATES in output: {len(out_ids)} rows but only {len(out_id_set)} unique ids "
                       f"({len(out_ids) - len(out_id_set)} duplicate rows)")

    missing = corpus_id_set - out_id_set
    extra = out_id_set - corpus_id_set
    if missing:
        errors.append(f"{len(missing)} corpus reviews MISSING from output, e.g. {list(missing)[:5]}")
    if extra:
        errors.append(f"{len(extra)} output ids NOT in corpus (shouldn't be possible), e.g. {list(extra)[:5]}")

    bad_label_rows = 0
    empty_label_rows = 0
    for r in out_rows:
        labels_raw = (r.get("labels") or "").strip()
        if not labels_raw:
            empty_label_rows += 1
            continue
        labels = [l.strip() for l in labels_raw.split("|") if l.strip()]
        if not labels:
            empty_label_rows += 1
            continue
        for l in labels:
            if l not in config.VALID_CODES:
                bad_label_rows += 1
                break
    if empty_label_rows:
        errors.append(f"{empty_label_rows} rows have empty/no labels")
    if bad_label_rows:
        errors.append(f"{bad_label_rows} rows contain a label outside the valid vocabulary")

    print()
    if errors:
        print("FAILED — issues found:")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"PASSED — {len(out_rows)} rows, exact 1:1 match with the {len(corpus_id_set)}-review corpus, "
              f"every row has a valid label. Stage 1 full-corpus classification is verified complete.")

if __name__ == "__main__":
    main()
