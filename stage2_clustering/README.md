# stage2_clustering/

Stage 2 (§4.4.2): embeds each review (instructor-large,
`sentence-transformers`) and clusters within each of the 17 taxonomy categories
independently, via UMAP (dimensionality reduction) + HDBSCAN (density clustering).

**This is the live rerun executed 2026-09-24, not the original run** — see
`STAGE2_RUN_LOG.md` for the full account: environment, exact package versions,
timing, and — critically — §6's cluster-by-cluster comparison against the
original write-up's Table 4.14. The live rerun produced **77 non-noise clusters**
(65,300 assignment rows, 8,912 noise rows), versus the original run's 65. This is
the disclosed, expected consequence of UMAP/HDBSCAN's own non-determinism (the
project's write-ups already attribute this to the clustering method's own
stochastic ANN search and SGD optimization, not to a bug), and it is the reason
every Stage 3/4 file downstream of this folder is also a "77-cluster, live-run"
artifact rather than a copy of the original 65-cluster results.

| File | What it is |
|---|---|
| `STAGE2_RUN_LOG.md` | The full run log — read this first. |
| `cluster_assignments.csv` | 67,300 rows: every review's (category, cluster_id) assignment, or -1 for noise. This is the file every downstream stage (Stage 3, BL1, BL2, the rubric) actually joins against. |
| `cluster_summary.csv` | 17 rows, one per taxonomy category: n_reviews, min_cluster_size parameter used, n_clusters found, n_noise, noise_pct. |
| `embed_log.txt` | Full timestamped embedding-step log (2h 19m, one uninterrupted pass — contrast with the original run's 37 relaunches across 8.5 hours). |
| `cluster_stdout.log` | Full clustering-step console output, every category. |
| `install_log.txt` | pip install output for the four packages installed this run (`sentence-transformers==6.0.1`, `torch==2.14.0`, `umap-learn==0.5.12`, `hdbscan==0.8.44`). |
| `embed_reviews.py`, `cluster_categories.py` | The exact scripts run, pointed at this run's actual input/output paths. |

**Not included, by design:** `embeddings.npy` (52,392 × 768 float32 matrix, 154MB)
and `review_ids.json` are not shipped in this package — they are fully
regeneratable from `embed_reviews.py` and not needed to redo the clustering step or
feed BL1. This is a disclosed omission, not a missing file.
