# stage2_clustering/

Stage 2 (§4.4.2): embeds each review (instructor-large,
`sentence-transformers`) and clusters within each of the 17 taxonomy categories
independently, via UMAP (dimensionality reduction) + HDBSCAN (density clustering).

Run executed 2026-09-24 — see `STAGE2_RUN_LOG.md` for the full account:
environment, exact package versions, timing, and full per-category results.
This run produced **77 non-noise clusters** across the 17 categories
(67,300 total assignment rows, 8,912 noise rows, 58,388 non-noise rows).
UMAP + HDBSCAN is a stochastic method, so re-running this stage is not
guaranteed to reproduce identical cluster counts even with a fixed random
seed.

| File | What it is |
|---|---|
| `STAGE2_RUN_LOG.md` | The full run log — read this first. |
| `cluster_assignments.csv` | 67,300 rows: every review's (category, cluster_id) assignment, or -1 for noise. This is the file every downstream stage (Stage 3, BL1, BL2, the rubric) actually joins against. |
| `cluster_summary.csv` | 17 rows, one per taxonomy category: n_reviews, min_cluster_size parameter used, n_clusters found, n_noise, noise_pct. |
| `embed_log.txt` | Full timestamped embedding-step log (2h 19m, one uninterrupted pass). |
| `cluster_stdout.log` | Full clustering-step console output, every category. |
| `install_log.txt` | pip install output for the four packages installed this run (`sentence-transformers==6.0.1`, `torch==2.14.0`, `umap-learn==0.5.12`, `hdbscan==0.8.44`). |
| `embed_reviews.py`, `cluster_categories.py` | The scripts run for this stage. **Note:** `BATCHES_DIR`/`LABELS_CSV` inside them are hardcoded to this run's execution environment — see the docstring note in each file before reusing them elsewhere. |

**Not included, by design:** `embeddings.npy` (52,392 × 768 float32 matrix, 154MB)
and `review_ids.json` are not shipped in this package — they are fully
regeneratable from `embed_reviews.py` and not needed to redo the clustering step or
feed BL1. This is a disclosed omission, not a missing file.
