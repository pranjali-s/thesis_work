# taxonomy/

This folder holds the **sampling** step of the B3 taxonomy-construction procedure
(§4.3.2) only — not the taxonomy itself. That distinction is deliberate and is
disclosed in detail in `taxonomy_sampling.py`'s own docstring; this README
summarizes it.

| File | What it is |
|---|---|
| `taxonomy_sampling.py` | Reconstructs the stratified sample of 360 Robinhood reviews (9 calendar quarters × 5 star ratings × 8 reviews/cell, seed 42) that the 16-category taxonomy was built from. |
| `b3_v2_reconstructed_sample.csv` | That script's output — the 360-review sample. |
| `combined_reviews.csv` | A duplicate of `data_collection/output/combined_reviews.csv`, kept here so the sampling script has a local input to run against. |

## Why this folder doesn't contain the taxonomy itself

Per `taxonomy_sampling.py`'s own docstring, two things are genuinely absent from
this project's accessible files, and this script does not attempt to fabricate
either:

1. **The category assignment step.** The taxonomy's 16 categories were produced by
   a human (or LLM) analyst reading all 360 sampled reviews in full and assigning
   free-text concern labels inductively — a qualitative judgment process, not a
   deterministic function of review text. There is no script that takes the 360
   reviews as input and outputs "16 categories" the way a classifier would.
2. **The Table 4.9 keyword-frequency script.** The write-up cites a "Pass 2
   keyword-pattern script" as the source of Table 4.9's frequency counts. That
   script could not be located anywhere in this project's accessible files — only
   a few truncated example keyword fragments appear in the write-up's prose. This
   script deliberately does not attempt to reconstruct it, since a reconstruction
   from partial examples would not reliably reproduce Table 4.9's exact counts,
   and presenting a guess as "the" original script would be misleading.

If either of these — the real Pass-1 category-assignment record, or the real Pass-2
keyword script — exists somewhere on your machine, adding them here (or telling
Claude where they are) would close a real, currently-disclosed gap in this
project's documentation trail. Nothing has been added or reconstructed here in
their place.

**Note also:** this sampling script draws from the same 18,442-review Robinhood
pool as the current two-platform corpus, consistent with the current pipeline —
but the original taxonomy's actual 360-review sample (and its resulting category
assignments) predates this two-platform re-run and cannot be regenerated
byte-for-byte from this script alone; it is a "reasonable reconstruction of the
sampling procedure," per the script's own docstring, not a guaranteed match to
whatever originally produced the taxonomy.
