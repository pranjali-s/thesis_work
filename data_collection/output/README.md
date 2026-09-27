# data_collection/output/

The real output of the two-platform (Google Play + Apple App Store) review
collection re-run described in `../README.md`, produced by running
`collect_reviews.py`.

| File | What it is |
|---|---|
| `combined_reviews.csv` | All three apps, both platforms — the 52,392-review corpus used by every downstream stage (Stage 1 classification, Stage 2 clustering, and all of Stage 4). |
| `collection_manifest.json` | Run metadata: collection timestamp, 24-month cutoff, resolved Apple numeric IDs per app, per-app/per-platform review counts, and the duplicate-ID check result (0 duplicates). |
| `reviews_<app>_google_play.csv` | Per-app, per-platform Google Play export (6 files total across the 3 apps: `reviews_robinhood_google_play.csv`, `reviews_coinbase_google_play.csv`, `reviews_trading_212_google_play.csv`). |
| `reviews_<app>_app_store.csv` | Per-app, per-platform Apple App Store export (`reviews_robinhood_app_store.csv`, `reviews_coinbase_app_store.csv`, `reviews_trading_212_app_store.csv`). |

Verified directly from `collection_manifest.json`: 52,392 total
reviews (Robinhood 18,442 / Coinbase 26,652 / Trading 212 7,298), 0 duplicate IDs
— consistent with every stage downstream that reports this same corpus size.

**Correction (2026-09-26):** an earlier version of this file stated that the
per-app, per-platform CSVs "were not seen in this folder listing." A fresh,
complete recursive listing of this folder taken 2026-09-26 confirms all six
per-platform CSVs listed above **are** present, alongside the combined file
and the manifest. That earlier note was incorrect and is corrected here.
