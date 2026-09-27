# stage1_classification/

Stage 1 (§4.4.1): LLM-based multi-label classification of reviews against the
17-category taxonomy, using `claude-sonnet-5` via direct Anthropic Messages Batches
API calls (not the subagent-orchestration harness batches 1-15 originally used —
see `full_corpus_classifier/README.md` for that revision history and its
~8-10x cost saving).

| Subfolder | What it does | Rows | Verified row count |
|---|---|---|---|
| `full_corpus_classifier/` | Classifies the entire 52,392-review corpus, 175 batches. | 52,392 | ✅ `stage1_full_corpus_labels.csv` = 52,392 data rows, exact match |
| `ground_truth_classification/` | Classifies the ~5,544 ground-truth reviews not already covered by the 616-review human reliability subsample. | 5,544 | ✅ `step6_ground_truth_labels.csv` = 5,544 data rows, exact match |
| `human_review_tool/` | A terminal tool for a human to manually code the 616-review reliability subsample (for computing human-vs-AI Cohen's kappa). | 616 | Not independently re-counted this session — see that folder's own README. |

## A note on each manifest's `total_reviews` figure

`full_corpus_classifier/manifest.json` reports `total_reviews: 53275` and
`ground_truth_classification/manifest.json` reports `total_reviews: 5653` — both
larger than the final, verified labels-file row counts above (52,392 and 5,544
respectively). This was checked directly this session and is **not a data-quality
problem**: those manifest figures are the sum of the 175 (or 19) *constructed
batches* before final combination/deduplication into the single labels CSV, not a
count of unique reviews classified. The labels CSVs — which are what every
downstream stage actually consumes — match the documented corpus sizes exactly.

## Known gap, not fabricated

`B4_ground_truth_frame_v2.csv` — the full ~6,160-row combined sampling frame that
both the 616-review reliability subsample and the ~5,544-review ground-truth set
are drawn from, and that is documented extensively in the project's
`Stage1_4.4.1_writeup.md` §4.4.1.7 — was not found anywhere in this
`stage1_classification/` tree. Only its two component splits are present (the
616-row subsample in `human_review_tool/`, and the ~5,544-row remainder in
`ground_truth_classification/`). If you have the combined frame file, adding it
here would close a real gap; it has not been reconstructed or guessed at in its
absence.

## ⚠ Cost incident, disclosed in `full_corpus_classifier/README.md`

The first attempt at the full-corpus run spent ~$8.87 producing no usable output,
because Claude Sonnet 5's adaptive thinking (on by default) consumed the entire
token budget before writing an answer. This is fixed in the current
`classify_reviews.py` (`"thinking": {"type": "disabled"}`) — see that folder's
README for the full incident writeup before re-running anything here.
