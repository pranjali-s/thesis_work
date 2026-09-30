# Stage 2 (Clustering) — Run Log

This is a real-time execution of Stage 2, run in this session on 2026-09-24 against the corpus and Stage 1 labels attached. Every timestamp, command, and number below is taken directly from this run's actual logs.

## 1. Inputs used

| File | Your upload | Rows | Notes |
|---|---|---|---|
| Review corpus | `1790252986366_combined_reviews.csv` | 52,392 | Columns: `app, platform, review_id_hash, review_text, rating, review_date, app_version, thumbs_up_count, developer_reply_present` |
| Stage 1 labels | `1790253002031_stage1_full_corpus_labels.csv` | 52,392 | Columns: `review_id_hash, labels` |

**Verified before running anything** (not assumed): both files parse to exactly 52,392 rows with zero duplicate `review_id_hash` values each. The two ID sets are exactly equal — 0 IDs only in the corpus, 0 IDs only in the labels file, intersection = 52,392. `review_text` is non-empty for all 52,392 rows. `rating` is non-empty for all 52,392 rows. `thumbs_up_count` is empty for 2,311 rows (4.41%) — this matches the figure independently documented in `Stage4_BL1_writeup.md` §4.4.4.7, a useful cross-check that this is the same underlying dataset. App breakdown: Robinhood 18,442 / Coinbase 26,652 / Trading 212 7,298 — matching the documented B2 v2 corpus composition.

## 2. Environment

Checked directly in this session before installing anything:

```
Python 3.11.15
CPU cores: 2
GPU: none (nvidia-smi not found)
```

Pre-installed at exactly the pinned versions already: `numpy 2.4.4`, `scikit-learn 1.8.0`.

Installed via `pip install --break-system-packages sentence-transformers==6.0.1 torch==2.14.0 umap-learn==0.5.12 hdbscan==0.8.44`. Resolved versions, confirmed after install via `importlib.metadata`:

```
sentence-transformers 6.0.1
torch                 2.14.0
umap-learn             0.5.12
hdbscan                0.8.44
numpy                  2.4.4
scikit-learn            1.8.0
torch.cuda.is_available() -> False   (CPU-only)
```

All six packages resolved to the exact pinned versions with no substitutions.

## 3. Step 1 — Embedding (`embed_reviews.py`)

Model: `hkunlp/instructor-large` via `sentence-transformers`, instruction prefix `"Represent the mobile app review for clustering by specific user concern:"`, `max_seq_length=160`. Checkpointed every 500 reviews.

**Started:** 2026-09-24 12:34:12 UTC
**Finished:** 2026-09-24 14:53:36 UTC
**Total elapsed:** 139.0 minutes (2h 19m)

Console confirmed at start: `"Corpus id set matches Stage 1 labels file exactly (52,392 expected)."`

Throughput held steady throughout at roughly 5.5–7.2 reviews/sec per 500-review chunk (full per-checkpoint log in `embed_log.txt`, included in this package). The running process was checked roughly every 6 minutes for the full duration — no crashes, no restarts needed; the run completed in one uninterrupted pass.

**Output:**
- `embeddings/embeddings.npy` — 52,392 × 768 float32 matrix, 154 MB. Verified after completion: shape matches ID count exactly, zero NaN values.
- `embeddings/review_ids.json` — the 52,392 review IDs in the exact order matching the embedding matrix rows.
- `embeddings/embed_log.txt` — the full per-checkpoint log (included in this package).

(The embeddings matrix itself is not included in the zip — 154 MB and not needed downstream for BL1 or for redoing the clustering step, since it's fully regeneratable from the same embed step. Ask if you want it sent separately.)

## 4. Step 2 — Clustering (`cluster_categories.py`)

UMAP (`n_components=5, n_neighbors=min(15,n-1), min_dist=0.0, metric="cosine", random_state=42`) followed by HDBSCAN (`min_cluster_size=max(8,n//60)` default, `metric="euclidean"`), run independently per one of 17 taxonomy categories, with four documented `CATEGORY_OVERRIDES` (`TRADE_EXECUTION`, `PREDICTION_MARKETS`, `ACCOUNT_LIFECYCLE`, `ADVERTISING_NOTIFICATIONS`).

**Started:** 2026-09-24 14:55:01 UTC
**Finished:** 2026-09-24 14:58:33 UTC (approximately — captured within the following poll)
**Total elapsed:** ~3.5 minutes

Console showed a UMAP warning (`n_jobs value 1 overridden to 1 by setting random_state`) — a library-level notice, not an error — appearing identically for every category.

**Output:**
- `clusters/cluster_assignments.csv` — 67,300 data rows (67,301 with header). Verified: 52,392 unique `review_id_hash` values (matching the full corpus — every review appears at least once), 17 unique categories, 8,912 noise rows (`cluster_id == -1`), 58,388 non-noise rows.
- `clusters/cluster_summary.csv` — 17 rows, one per category.

## 5. Results by category

| Category | n_reviews | min_cluster_size | n_clusters | n_noise | noise_pct |
|---|---|---|---|---|---|
| ACCOUNT_ACCESS_AUTH | 4,289 | 71 | 2 | 0 | 0.0% |
| ACCOUNT_LIFECYCLE | 1,486 | 80 | 6 | 377 | 25.4% |
| ADVERTISING_NOTIFICATIONS | 752 | 80 | 3 | 232 | 30.9% |
| APP_STABILITY_PERFORMANCE | 4,380 | 73 | 4 | 108 | 2.5% |
| ASSET_COVERAGE | 1,061 | 17 | 4 | 54 | 5.1% |
| CHARTING_TOOLS | 1,018 | 16 | 2 | 5 | 0.5% |
| CRYPTO_SPECIFIC | 2,609 | 43 | 5 | 194 | 7.4% |
| CUSTOMER_SUPPORT | 4,452 | 74 | 2 | 0 | 0.0% |
| FEES_SUBSCRIPTION | 2,879 | 47 | 7 | 572 | 19.9% |
| FUNDS_TRANSFER | 4,136 | 68 | 3 | 0 | 0.0% |
| GENERAL_SENTIMENT | 17,435 | 290 | 7 | 4,890 | 28.0% |
| ONBOARDING_BEGINNER | 4,279 | 71 | 5 | 21 | 0.5% |
| PREDICTION_MARKETS | 303 | 30 | 3 | 55 | 18.2% |
| SECURITY_PRIVACY | 1,532 | 25 | 10 | 299 | 19.5% |
| TRADE_EXECUTION | 2,170 | 80 | 2 | 296 | 13.6% |
| TRUST_FAIRNESS_REGULATORY | 2,272 | 37 | 4 | 218 | 9.6% |
| USABILITY_NAV | 12,247 | 204 | 8 | 1,591 | 13.0% |

77 non-noise clusters total across the 17 categories.

## 6. What's in the downloadable package

| File | What it is |
|---|---|
| `STAGE2_RUN_LOG.md` | This file. |
| `cluster_assignments.csv` | The real output — 67,300 rows. This is the file BL1 needs. |
| `cluster_summary.csv` | Per-category summary table (Section 5 above, as CSV). |
| `embed_log.txt` | Full timestamped embedding log, every checkpoint. |
| `cluster_stdout.log` | Full clustering console output, every category. |
| `install_log.txt` | Full pip install output for the four packages installed this run. |
| `embed_reviews.py`, `cluster_categories.py` | The exact scripts run, with paths pointed at this run's actual input files. |

## 7. Next step

`cluster_assignments.csv` from this package is what you feed into the BL1 redo package (`compute_cluster_features.py` / `verify_bl1_independent.py`), together with the same corpus file you uploaded here (it already has `rating` and `thumbs_up_count`, so it covers both stages).
