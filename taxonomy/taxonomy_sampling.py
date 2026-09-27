"""
B3 (v2 redo) -- Taxonomy pilot sampling procedure, reconstructed for local
verification.

WHAT THIS SCRIPT DOES
----------------------
Reconstructs the stratified-sampling step described in the project's
"4.3_Taxonomy_writeup_v2.md" (Section 4.3.2, "Sampling"):

    "The pilot sample is drawn from the 18,442 Robinhood reviews in the
    new two-platform corpus (4.2), stratified by calendar quarter and star
    rating... Eight reviews were drawn at random (seed 42) from each of
    the 9 quarters x 5 star ratings = 45 cells, giving n = 360."

WHAT THIS SCRIPT DOES **NOT** DO, AND WHY -- READ THIS BEFORE RUNNING
-----------------------------------------------------------------------
This script reproduces the SAMPLING step only. It does NOT, and cannot,
reproduce the taxonomy itself. The taxonomy's 16 categories were produced
by Pass 1 of the B3 procedure -- an analyst (in this project, an LLM)
reading all 360 sampled reviews in full and assigning free-text concern
labels inductively, with no predetermined category list. That is a
qualitative judgment process, not a deterministic function of the review
text, so there is no script that takes these 360 reviews as input and
outputs "16 categories" the way a classifier would. If you run this
script, you will get the correct 360-review SAMPLE (assuming your local
copy of the corpus and this script's cell/quarter logic match), but you
will not get category assignments -- those require actually reading the
reviews (by a person, or by prompting an LLM per-review the way this
project's Stage 1 classification does; see stage1_claude/TAXONOMY_PROMPT.txt
in the project files for the prompt actually used for that separate,
full-corpus classification step).

Separately: the write-up also cites a "Pass 2 keyword-pattern script" as
the source of Table 4.9's frequency counts. That script could not be
located anywhere in this project's accessible files -- only a few example
keyword fragments appear in the write-up's prose (e.g. for
ACCOUNT_ACCESS_AUTH: "login|password|verif|biometric|selfie|locked out|
other device|..." -- note the truncation). This script does not attempt to
reconstruct that keyword script, because doing so from partial examples
would not reliably reproduce Table 4.9's exact counts, and presenting a
reconstruction as "the" original script would be misleading. This gap is
disclosed here rather than papered over.

REQUIREMENTS
------------
Your own copy of the v2 combined_reviews.csv (the 52,392-row, two-platform
corpus: columns app, platform, review_id_hash, review_text, rating,
review_date, app_version, thumbs_up_count, developer_reply_present).
Point INPUT_CSV at your local copy.

USAGE
-----
    python3 b3_v2_stratified_sampling.py /path/to/combined_reviews.csv
"""
import csv
import sys
import random
from collections import defaultdict
from datetime import datetime

SEED = 42
N_PER_CELL = 8


def parse_quarter(review_date: str) -> str:
    """Calendar quarter, e.g. '2024Q3', from an ISO-ish review_date string."""
    date_part = review_date[:19].replace("T", " ")
    dt = datetime.strptime(date_part[:19], "%Y-%m-%d %H:%M:%S")
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}Q{q}"


def main(input_csv: str, app_name: str = "Robinhood"):
    rows = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["app"] == app_name:
                rows.append(row)

    print(f"{app_name} reviews in pool: {len(rows)}")

    cells = defaultdict(list)
    for row in rows:
        q = parse_quarter(row["review_date"])
        rating = row["rating"]
        cells[(q, rating)].append(row)

    print(f"Number of (quarter, rating) cells: {len(cells)}")
    min_cell = min(cells.items(), key=lambda kv: len(kv[1]))
    print(f"Smallest cell: {min_cell[0]} with {len(min_cell[1])} reviews "
          f"(write-up claims minimum was 29)")

    # Deterministic draw: sort cell keys, sort each cell's rows by
    # review_id_hash before sampling, so the draw is reproducible given a
    # fixed seed -- this is a REASONABLE reconstruction of "drawn at random
    # (seed 42)", not a guaranteed bit-for-bit match to whatever exact
    # code/library produced the original write-up's sample, since that
    # original sampling script was not found in the project's files
    # (disclosed in the module docstring above).
    rng = random.Random(SEED)
    sample = []
    for key in sorted(cells.keys()):
        cell_rows = sorted(cells[key], key=lambda r: r["review_id_hash"])
        n = min(N_PER_CELL, len(cell_rows))
        sample.extend(rng.sample(cell_rows, n))

    print(f"Total sampled: {len(sample)} (expect 360 if every cell had >= 8)")

    out_path = "b3_v2_reconstructed_sample.csv"
    if sample:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(sample[0].keys()) + ["year_quarter"])
            writer.writeheader()
            for row in sample:
                out_row = dict(row)
                out_row["year_quarter"] = parse_quarter(row["review_date"])
                writer.writerow(out_row)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])