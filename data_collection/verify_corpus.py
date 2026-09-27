"""Post-collection data-quality verification, mirroring 4.2.3's original
checks so the new two-platform corpus gets the same scrutiny: duplicate
IDs, missing-value patterns, residual non-English content, and per-app /
per-platform composition. Run this before treating collect_reviews.py's
output as the new corpus.

Usage:
    python verify_corpus.py [path/to/combined_reviews.csv]
"""

import csv
import sys
from collections import Counter

from language_filter import is_majority_non_ascii

DEFAULT_PATH = "output/combined_reviews.csv"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows from {path}\n")

    # --- duplicate IDs -----------------------------------------------
    id_counts = Counter((r["app"], r["platform"], r["review_id_hash"]) for r in rows)
    dup_keys = [k for k, c in id_counts.items() if c > 1]
    print(f"Duplicate (app, platform, review_id_hash) keys: {len(dup_keys)}")
    if dup_keys:
        print(f"  e.g. {dup_keys[:5]}")

    # --- per app / per platform composition ---------------------------
    comp = Counter((r["app"], r["platform"]) for r in rows)
    print("\nComposition by app x platform:")
    for (app, platform), n in sorted(comp.items()):
        pct = 100 * n / len(rows) if rows else 0
        print(f"  {app:14s} {platform:12s} {n:6d}  ({pct:5.1f}%)")

    # --- missing-value patterns ----------------------------------------
    print("\nMissing-value counts by field:")
    for field in rows[0].keys() if rows else []:
        missing = sum(1 for r in rows if r[field] in ("", "None", None))
        if missing:
            pct = 100 * missing / len(rows)
            print(f"  {field:24s} {missing:6d} missing ({pct:5.1f}%)")

    # --- residual non-English content ----------------------------------
    non_english = [r for r in rows if is_majority_non_ascii(r["review_text"])]
    print(f"\nResidual majority-non-ASCII reviews after filtering: {len(non_english)} "
          f"({100 * len(non_english) / len(rows):.3f}% of corpus)" if rows else "")
    if non_english:
        print("  These slipped through the filter or were added after it ran — inspect them.")

    # --- exact-text duplication within an app (same signal as original) ---
    text_counts = Counter((r["app"], r["review_text"]) for r in rows if r["review_text"])
    repeated = sum(c for c in text_counts.values() if c > 1)
    print(f"\nReviews sharing exact text with another review from the same app: {repeated} "
          f"({100 * repeated / len(rows):.1f}%)" if rows else "")

    # --- rating distribution --------------------------------------------
    print("\nRating distribution by app:")
    ratings = Counter((r["app"], r["rating"]) for r in rows)
    for app in sorted(set(r["app"] for r in rows)):
        dist = {str(k[1]): v for k, v in ratings.items() if k[0] == app}
        print(f"  {app:14s} {dict(sorted(dist.items()))}")


if __name__ == "__main__":
    main()