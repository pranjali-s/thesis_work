# PranjaliThesis — technical materials index

This folder is the real, local record of the technical work behind the "User-Need
Mining for Retail Trading Apps" thesis pipeline (Robinhood, Coinbase, Trading 212).
Everything here was executed on this machine or fetched from real, live sources —
it is the primary-source evidence that substantiates the write-ups and numbers
documented in the Claude project ("Thesis 2").

This index and every other `README.md` under this tree were added on 2026-09-26 by
Claude, at your request, after reading the folder structure and (where staging
succeeded) the actual file contents — run logs, manifests, and existing READMEs —
rather than guessing from file names alone. Where a claim below could not be
verified from file content this session, that is said explicitly.

## Folder map

| Folder | Stage | What it holds |
|---|---|---|
| `data_collection/` | §4.2 | Scrapers for Google Play + Apple App Store reviews, and the resulting 52,392-review two-platform corpus. |
| `taxonomy/` | §4.3 (B3) | The stratified-sampling script for the 360-review taxonomy pilot sample — **not** the taxonomy category assignment itself (see that folder's own README for why). |
| `stage1_classification/` | §4.4.1 | LLM-based multi-label classification of the full corpus (175 batches) and of a separate ~5,544-review ground-truth set, plus the human-coding tool for the 616-review reliability subsample. |
| `stage2_clustering/` | §4.4.2 | Embedding (instructor-large) + per-category UMAP/HDBSCAN clustering. This copy is the **live 77-cluster rerun** (2026-09-24), not the original 65-cluster run. |
| `stage3_summarization/` | §4.4.3 | LLM-generated structured "roadmap items" (title/description/quotes) per cluster, with independent grounding verification and blind adversarial rating. Also the live rerun, chained off this folder's own Stage 2 output. |
| `stage4_prioritization/` | §4.4.4 / RQ4b | The three competing prioritization methods — BL1 (rule-based ClusterScore), BL2 (trained Random Forest), and the LLM rubric — plus E1 (real release-note collection), E2 (cluster-to-release matching), and E4 (rank-agreement evaluation of all three methods against E2). |

`venv/` (Python virtual environment) is also present at the root but is not thesis
material and was not documented.

## Important: this is the live rerun, not the original run

Every Stage 2/3/4 artifact in this folder is dated **2026-09-24** and is explicitly
labeled in its own run log as a **live, from-scratch rerun** executed after the
original session's workspace was lost — not a copy of the original run's output.
The rerun's Stage 2 clustering produced **77 non-noise clusters**, where the
original, now-lost run produced **65**. This single fact (documented in
`stage2_clustering/STAGE2_RUN_LOG.md` §6) is the root cause of nearly every
downstream number in `stage3_summarization/` and `stage4_prioritization/` differing
from the original write-ups' tables — it is disclosed, expected non-determinism in
the UMAP/HDBSCAN pipeline, not an error, a data-quality problem, or a discrepancy
introduced by this rerun's own code. Each stage's run log makes its own
original-vs-rerun comparison explicit; the project's own write-ups (e.g.
`Stage4_CONSOLIDATED_LIVE_writeup.md`) already incorporate this rerun's numbers as
the current, cited results, so nothing here needed to be reconciled or corrected —
it already **is** the source data the write-ups cite.

## What was checked this session, and what it found

Per your request to check correctness and flag anything missing, here is a plain
summary of what was verified against real file content (not just file names/sizes)
this session, and the handful of things worth your attention:

**Confirmed consistent (no action needed):**
- `stage1_classification/full_corpus_classifier/stage1_full_corpus_labels.csv` has
  exactly 52,392 data rows — an exact match to the corpus size documented
  everywhere in the project. (Its `manifest.json` separately reports
  `total_reviews: 53275` — that is the sum of the 175 *constructed batches* before
  final deduplication/combination, not the row count of the final labels file; the
  two numbers describe different points in the pipeline, not a real discrepancy.)
- `stage1_classification/ground_truth_classification/step6_ground_truth_labels.csv`
  has exactly 5,544 data rows — an exact match to the "~5,544 ground-truth reviews"
  figure used elsewhere in the project. (Its `manifest.json` similarly reports a
  pre-combination `total_reviews: 5653`, for the same reason as above.)
- `stage3_summarization/grounding_check_report.json` is genuinely complete despite
  being only 101 bytes — it is a compact summary (`{"total_quotes":231,
  "unknown_id":[],"wrong_cluster":[],"ungrounded":[],"passed":true}`), not a
  truncated or broken file.
- The 77 files in `stage3_summarization/prep/` sum to exactly 77 clusters across
  all 17 taxonomy categories, matching Stage 2's live 77-cluster output exactly.

**Worth your attention:**
- **Two separate, non-identical E1 (release-note) collection tools exist locally**:
  `stage4_prioritization/e1_release_note_scraper/collect_company_updates.py` (a
  broader research scraper — Robinhood newsroom, Coinbase blog, Trading 212
  Discourse + Apple version history, producing `company_articles.csv`,
  `feature_candidates.csv`, `apple_version_history.csv`, etc.) and
  `stage4_prioritization/bl2_random_forest/build_e1.py` (a simpler, separate
  script). **Only `build_e1.py`'s output (`e1_release_notes.csv`, 147 rows) is
  what actually fed BL2 and E4** in this run's `BL2_LIVE_RUN_LOG.md` /
  `E4_LIVE_RUN_LOG.md`. The more elaborate `collect_company_updates.py` scraper's
  own README says its live company-page crawling "remains unverified in this
  execution environment" and its packaged output
  (`verified_examples_no_start_limit_2026-09-24.csv`) is only 23 manually-checked
  examples — it does not appear to be the source of the 147-row dataset BL2/E4
  actually used. See both folders' own READMEs for the full detail. This isn't
  necessarily wrong, but it's easy to mix up which script produced the numbers
  actually cited in the thesis, so it's flagged here explicitly.
- **A file referenced in the project's Stage 1 write-up appears to be genuinely
  absent here**: `B4_ground_truth_frame_v2.csv` (the full ~6,160-row combined
  sampling frame that `stage1_full_corpus_labels.csv`'s reliability subsample and
  the ground-truth set are drawn from) was not found anywhere in
  `stage1_classification/`. Only its two component splits appear present
  (`B4_human_reliability_subsample_v2.csv` in `human_review_tool/`, and
  `remaining_ground_truth.csv` in `ground_truth_classification/`). If you have this
  file, it would be worth adding it to `human_review_tool/` or a shared location —
  it was not fabricated or reconstructed here.
- **`taxonomy/` is deliberately thin.** This is not something to "fix" by adding a
  script — see `taxonomy/README.md` for why the category-assignment step and the
  Table 4.9 keyword-frequency script are genuinely not present anywhere in this
  project's accessible files, and should not be silently reconstructed.

Nothing else was added to this folder tree beyond `README.md` files — no data,
scripts, or run outputs were fabricated, reconstructed, or altered.
