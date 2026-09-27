# reference_snapshot_2026-09-24/

A real, dated snapshot of Apple App Store version-history data for all three apps,
obtained live on 2026-09-24 (per `../README.md`'s Validation section) — kept
separate from `../output/` because it was fetched directly rather than through
`collect_company_updates.py`'s full pipeline.

| File | What it is |
|---|---|
| `apple_version_history.csv` | All 75 visible version entries across the three apps' public App Store pages, with `version_date` and source hashes. |
| `apple_feature_notes.csv` | Only version notes that *appear* to name a specific change, after generic-text filtering. **Empty (header only) this snapshot** — all 75 visible versions had only generic release-note text ("bug fixes and performance improvements" style), not that there were no real app changes. Human review of `apple_version_history.csv` directly is still required to find genuine feature notes. |
| `snapshot_manifest.json` | Date window and coverage metadata for this specific snapshot. |

Per the parent folder's README, Apple HTML parsing itself was validated against a
live public fetch this same day — it is the company-page crawl (newsroom/blog/
Discourse), not this Apple snapshot, that remains unverified in this execution
environment.
