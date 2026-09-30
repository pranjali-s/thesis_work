# stage4_prioritization/bl2_random_forest/

**BL2**: a trained-classifier baseline adapted from Scalabrino et al. (2017, IEEE
TSE, DOI 10.1109/TSE.2017.2759112) — a Random Forest predicting whether a cluster
was addressed in a later app release, trained on `n_reviews`, `avg_rating`,
`delta_rating_app` (cluster rating vs. its app's baseline), and
`n_distinct_app_versions` (this project's substitute for the original paper's
`|devices|`, which requires Google Play device data this project has no access
to). This folder also contains this run's **E1** (live release-note collection)
and **E2** (cluster-to-release matching) — see below for why those had to be
redone here rather than just BL2.

## Why E1/E2 live here, not in a separate folder

Stage 2/3/BL1 could be safely rebuilt from this project's own detailed written
specs when the original workspace was lost. E1 is different — it's a snapshot of
real, dated, external release-note content, and the original 156-row E1 dataset
plus the original E2 outputs were not recoverable from anywhere in this project.
Reconstructing E1 "from memory" would mean fabricating plausible-looking release
notes — forbidden by this project's standing transparency rule. Given that choice,
the actual live re-fetch documented here was chosen deliberately, not defaulted
into.

| File | What it is |
|---|---|
| `BL2_LIVE_RUN_LOG.md` | The full run log — read this first. |
| `e1_release_notes.csv` | **147 real, dated release notes** (94 Trading 212 / 16 Robinhood / 37 Coinbase) — see `build_e1.py`. This is the E1 dataset that actually feeds everything below and `../e4_rubric/`. |
| `candidate_matching.py` → `e2_candidates.json` | TF-IDF + cosine-similarity top-3 release-note candidates per cluster (77 × 3). |
| `review_e2_matches.py` → `e2_human_labels.csv`, `e2_final.csv`/`.json` | Content-grounded match/no-match verdict per cluster, with disclosed reasoning per row. **Result this run: 0/77 matched (0.0%).** |
| `compute_bl2_features.py` → `cluster_features_bl2.json` | The 4 BL2 features per cluster. `delta_rating_app`'s exact formula (not given byte-for-byte in the original write-up) is disclosed here as reconstructed directly from the original's prose description. |
| `train_bl2.py` → `bl2_metadata.json`, `bl2_predictions.csv` | Random Forest training via Leave-One-Out CV. |
| `build_e1.py`, `*_stdout.log` | The exact scripts and full console output for every step above. |

## The headline finding — read before citing any BL2 number

**This run's E2 ground truth has 0 positive examples out of 77 clusters.** A
classifier cannot learn a positive-class decision boundary from zero positive
examples — this is disclosed as a direct, mechanical consequence of the label
distribution, not a training failure. Precision, recall, F1, and ROC-AUC for the
positive class are **undefined**, not zero. The reported LOOCV "accuracy: 1.0000"
is degenerate and must not be read as a good result — it is what you get, trivially,
when a model can only ever predict "negative" and every held-out example is
negative by construction. SMOTE cannot run at all (needs ≥1 positive to
interpolate from). This project's E1/E2 pipeline does not produce enough genuine,
content-verified cluster-to-release matches, in this run's data, to train or
validate a classifier baseline.

## Cross-reference: a second, separate E1 scraper exists elsewhere

`../e1_release_note_scraper/` contains a different, more elaborate release-note
scraper that was **not** the source of this folder's `e1_release_notes.csv` — see
`../README.md` and that folder's own README for the distinction. Don't assume the
two are interchangeable or that one supersedes the other without checking which
numbers you're trying to trace.
