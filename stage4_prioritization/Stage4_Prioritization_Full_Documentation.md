# Stage 4 — Roadmap Prioritization (`stage4_prioritization/`)

**Full documentation, verified file inventory, and reproduction guide.**
Everything under "Independently verified this session" was checked directly
against the actual files in this folder tree (cluster counts, score
distributions, E1/E2 counts, training labels, pairwise correlations — all
recomputed from `cluster_features.json`, `bl2_metadata.json`,
`e1_release_notes.csv`, `e2_final.csv`, `e4_results_live.json`, and
`stage4_scores_merged_live.json` themselves) — not copied from the folder's
own README/log claims. Where something could not be verified from these
files alone, that's stated explicitly.

All old-run comparison language has been removed from this folder's
documentation and scripts (READMEs, run logs, script docstrings, and the
two data fields that had a comparison baked into their stored text —
`bl2_metadata.json`'s `headline_finding` and `e2_human_labels.csv`'s
per-row disclosure note). Every file below describes this run's own data
only.

---

## 1. What this folder is

This is **Stage 4 of the pipeline (§4.4.4 / RQ4b)**: three competing
methods for ranking Stage 3's 77 roadmap items by priority, plus an
evaluation pipeline that checks whether any of them tracks what the three
companies (Trading 212, Robinhood, Coinbase) actually shipped. Four
subsystems, all from the live rerun (2026-09-24), chained off this same
tree's `stage2_clustering/` and `stage3_summarization/` output:

| Subfolder | What it is | RQ role |
|---|---|---|
| `bl1_ClsuterScore/` | **BL1** — rule-based `ClusterScore` formula from Wei et al. (2023), reused unmodified. Pure arithmetic, no LLM/human judgment. | Baseline 1 |
| `bl2_random_forest/` | **BL2** — trained Random Forest baseline adapted from Scalabrino et al. (2017/2019, see §9). Also contains this run's live **E1** (release-note collection) and **E2** (cluster-to-release matching), since BL2 needs E2's labels to train against. | Baseline 2, + E1/E2 |
| `e1_release_note_scraper/` | A separate, more elaborate release-note/version-history scraper. **Not** the E1 source that actually fed BL2/E4 this run (see §9). | Adjacent tooling, out of the audited pipeline |
| `e4_rubric/` | The **LLM-applied 6-dimension prioritization rubric**, and **E4**, the rank-agreement evaluation comparing rubric/BL1/BL2 against E2's ground truth and against each other. | RQ4b's headline evaluation |

---

## 2. Verified file inventory

### 2.1 `bl1_ClsuterScore/` (8 files)

| File | What it is | Verified this session |
|---|---|---|
| `README.md` | Folder overview | ✅ Present |
| `BL1_LIVE_RUN_LOG.md` | Full run log | ✅ Present, read in full |
| `compute_cluster_features.py` | Computes `bl1_cluster_score` per cluster from Stage 2's assignments + corpus | ✅ Present, read in full |
| `verify_bl1_independent.py` | Independently re-derives the score from raw files, 1e-6 tolerance | ✅ Present, read in full |
| `cluster_features.json` | Per-cluster features for all 77 clusters | ✅ Present; **independently recomputed: 77 clusters, min 7.38 / max 3468.40 / mean 405.69 / median 102.22 — exact match to the run log** |
| `bl1_ranking.csv` | The 77-row ranking (real deliverable) | ✅ Present |
| `compute_stdout.log`, `verify_stdout.log` | Console output | ✅ Present |

### 2.2 `bl2_random_forest/` (20 files)

| File | What it is | Verified this session |
|---|---|---|
| `README.md` | Folder overview | ✅ Present |
| `BL2_LIVE_RUN_LOG.md` | Full run log | ✅ Present, read in full |
| `build_e1.py` → `e1_release_notes.csv` | Live E1 collection (147 rows) | ✅ Present; **independently recomputed: 147 rows, 94 Trading 212 / 16 Robinhood / 37 Coinbase; 85 in-window / 62 out-of-window (window = 2024-06-01 to 2026-09-24) — exact match** |
| `candidate_matching.py` → `e2_candidates.json` | TF-IDF/cosine top-3 candidates per cluster | ✅ Present |
| `review_e2_matches.py` → `e2_human_labels.csv`, `e2_final.csv`/`.json` | Content-grounded match verdicts | ✅ Present; **independently recomputed: 77 rows, 0 matched — exact match** |
| `compute_bl2_features.py` → `cluster_features_bl2.json` | The 4 BL2 features per cluster | ✅ Present |
| `train_bl2.py` → `bl2_metadata.json`, `bl2_predictions.csv` | Random Forest, LOOCV | ✅ Present; **independently recomputed: n_positive=0, n_negative=77, LOOCV accuracy 1.0000 (degenerate), all positive-class metrics undefined — exact match** |
| `*_stdout.log` (5 files) | Console output for each step | ✅ Present |

### 2.3 `e1_release_note_scraper/` (separate tooling, not part of the audited E1→E2→BL2→E4 chain)

| File / folder | What it is | Verified this session |
|---|---|---|
| `README.md` | Discloses this scraper's own live-crawling was unverified in its execution environment | ✅ Present, read in full |
| `collect_company_updates.py`, `apple_history.py`, `build_example_dataset.py` | The scraper's source | ✅ Present |
| `verified_examples_no_start_limit_2026-09-24.csv` | 23 manually-checked example rows — a different size/shape from the 147-row dataset actually used downstream | ✅ Present, confirmed 23 rows |
| `verified_starting_set_2026-09-24.csv`, `reference_snapshot_2026-09-24/`, `output/` | Supporting scraper output | ✅ Present |

### 2.4 `e4_rubric/` (15 files)

| File | What it is | Verified this session |
|---|---|---|
| `README.md` | Folder overview | ✅ Present |
| `Rubric_LIVE_RUN_LOG.md` | Full run log for the rubric | ✅ Present, read in full |
| `E4_LIVE_RUN_LOG.md` | Full run log for E4 | ✅ Present, read in full |
| `rubric_judgment_scores.py` | Genuine per-cluster judgment source for actionability/overall_priority | ✅ Present, read in full |
| `build_stage4_rubric.py` → `stage4_scores_merged_live.json` | Merged 77-row rubric output | ✅ Present; **independently recomputed: 77 rows, min 1 / max 10 / mean 4.53 / median 4, distribution {1:30, 2:1, 3:4, 4:4, 5:2, 6:8, 7:10, 8:7, 9:5, 10:6} — exact match** |
| `verify_stage4_rubric_merge_live.py` | Independent merge re-derivation | ✅ Present |
| `compute_e4_live.py` → `e4_results_live.json`, `e4_rankings_full_live.csv` | Precision@k/MRR/Spearman vs. E2, pairwise Spearman | ✅ Present; **independently recomputed: rubric vs. BL1 rho = 0.4078 (p = 0.000232) — exact match** |
| `verify_e4_independent_live.py` | Independent re-derivation of E4's numbers | ✅ Present |
| `stage4_input_items_live.json` | 77 clusters merged with 5 deterministic dimensions | ✅ Present |
| `*_stdout.log` (2 files) | Console output | ✅ Present |

**All files each run log claims should exist are present across all four subsystems. No gaps in file inventory.**

---

## 3. Verified results (recomputed fresh this session from the raw data files)

### 3.1 BL1 — rule-based ClusterScore

`ClusterScore = (w_rev·|reviews| + w_th·|thumbsup|) / (w_ra·rating)`, weights (1, 0.1, 1), Wei et al. (2023, arXiv:2311.03058), unmodified.

| Metric | Value |
|---|---:|
| Clusters scored | 77 |
| Minimum score | 7.38 (Charting, Analytics & Professional Tools / 0) |
| Maximum score | 3,468.40 (Customer Support Quality / 1) |
| Mean | 405.69 |
| Median | 102.22 |
| Independent verification | 77/77 matched to 1e-6, 0 mismatches |

Known limitation reconfirmed on this run's own data: General Sentiment/3 (7,740 reviews, 4.43★) ranks 4th; Security & Data Privacy/6 (30 reviews, 1.07★, the single lowest-rated cluster of all 77) ranks only 68th — the formula has no severity floor or size normalization.

### 3.2 E1 — live release-note collection

| App | Total | In-window (2024-06-01 to 2026-09-24) | Out-of-window |
|---|---:|---:|---:|
| Trading 212 | 94 | 34 | 60 |
| Robinhood | 16 | 14 | 2 |
| Coinbase | 37 | 37 | 0 |
| **Total** | **147** | **85** | **62** |

Trading 212 confirmed exhaustive (Discourse API paginated to an empty page). Robinhood and Coinbase are real, dated content but explicitly not exhaustive collections.

### 3.3 E2 — candidate matching and match review

TF-IDF + cosine similarity (title+description, `max_features=5000`), same-app-preferred ranking, top-3 candidates per cluster, restricted to the 85 in-window notes. **Result: 0/77 matched (0.0%).** 10 of the highest-scoring candidates were individually content-verified (full article text fetched and read); all rejected on specific, documented grounds (see `e2_human_labels.csv`).

**Supplementary check, this session:** the 62 out-of-window notes (all published 2020-02-06 to 2024-05-28, i.e. entirely before the review corpus's own date range) were also matched and reviewed against the same 77 clusters, using the same methodology and match criteria. Top score 0.3791 (FEES_SUBSCRIPTION/6 ↔ a Trading 212 cash-ISA launch announcement); all top-10 candidates individually reviewed and rejected on specific grounds (keyword collisions, cross-app fallback because 0 of the 37 Coinbase notes are out-of-window, or the candidate predating the complaints by construction). **Result: 0 additional genuine matches.** This supplementary check was not logged as a pipeline artifact (no new file was written to this folder for it, per the user's explicit instruction for that session turn) — it is recorded here as a verified finding, not as a new file in the package.

### 3.4 BL2 — Random Forest baseline

Features: `n_reviews`, `avg_rating`, `delta_rating_app`, `n_distinct_app_versions`. LOOCV, 100 trees, `max_features="sqrt"`, unlimited depth, `random_state=42`.

| Metric | Value |
|---|---:|
| Positive / negative examples | 0 / 77 |
| LOOCV accuracy | 1.0000 (degenerate — predicts "negative" for every cluster) |
| Precision / recall / F1 / ROC-AUC (positive class) | Undefined (not zero) |
| SMOTE | Cannot run (needs ≥1 positive to interpolate from) |
| `delta_rating_app` range | −2.5697 to +1.2817 |
| `n_distinct_app_versions` range | 17 to 445 |
| Missing `app_version` among cluster members | 8,039 / 58,388 (13.77%) |

### 3.5 Rubric — 6-dimension LLM-applied prioritization

Reach, severity, engagement, recency, cross-platform generality computed deterministically; actionability and overall_priority genuinely judged per cluster (77/77, 0 missing).

| Metric | Value |
|---|---:|
| Clusters scored | 77 |
| `overall_priority` min / max / mean / median | 1 / 10 / 4.53 / 4 |
| Distribution (1→10) | 30, 1, 4, 4, 2, 8, 10, 7, 5, 6 |
| Clusters at floor (score 1) | 30 (39%) — all pure positive-sentiment clusters |
| Clusters at ceiling (score 10) | 6 — ACCOUNT_ACCESS_AUTH/1, APP_STABILITY_PERFORMANCE/2, APP_STABILITY_PERFORMANCE/3, CUSTOMER_SUPPORT/1, FUNDS_TRANSFER/0, TRADE_EXECUTION/1 |
| Independent merge verification | Key equality, no duplicates, field fidelity (0 mismatches/77), scale bounds (0 out-of-scale/539 values) — all passed |

### 3.6 E4 — rank-agreement evaluation

| Metric | Value |
|---|---:|
| E2 ground-truth positives | 0/77 |
| Precision@k / MRR / Spearman vs. ground truth, all 3 methods | Undefined (0 positive examples — not zero, not computable) |
| Rubric vs. BL1 pairwise Spearman | rho = 0.4078, p = 0.000232 |
| Rubric vs. BL2, BL1 vs. BL2 | Undefined (BL2's output has zero variance — trained on an all-negative target) |
| Independent verification | Recomputed from the three raw source files directly — 0 mismatches |

---

## 4. Environment needed for reproduction

| Requirement | Detail |
|---|---|
| Python | 3.11 (this run used 3.11.15) |
| Third-party packages | `scikit-learn` (1.8.0 this run), `imbalanced-learn` (0.14.2 this run, only needed if E2 ever finds ≥1 positive so SMOTE can run), `scipy` (for `spearmanr`) |
| LLM access | Claude Sonnet 5, invoked directly within this session for E2's match review and the rubric's actionability/overall_priority judgment — not a separate scripted API call |
| Web access | Needed for E1's live collection (`build_e1.py`) — Trading 212's Discourse JSON API, Robinhood's newsroom/sitemap, Coinbase's blog listing pages, plus individual article fetches |
| Input | Stage 1's review corpus, Stage 2's `cluster_assignments.csv`, Stage 3's `stage3_roadmap_items.json` and `prep/` folder |

---

## 5. A real reproduction blocker: hardcoded, session-specific paths

Every script below hardcodes absolute paths from the cloud session that actually ran it, none of which exist in this uploaded folder's own structure:

```python
# bl1_ClsuterScore/compute_cluster_features.py, verify_bl1_independent.py
ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
CORPUS_CSV = "/home/claude/Stage2_live/batches/batch_001.csv"

# bl2_random_forest/candidate_matching.py
ROADMAP_JSON = "/home/claude/Stage3_live/stage3_roadmap_items.json"
PREP_DIR = "/home/claude/Stage3_live/prep"

# bl2_random_forest/compute_bl2_features.py
ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
CORPUS_CSV = "/home/claude/Stage2_live/batches/batch_001.csv"
BL1_FEATURES_JSON = "/home/claude/BL1_live/cluster_features.json"

# e4_rubric/compute_e4_live.py, verify_e4_independent_live.py
"/home/claude/BL1_live/bl1_ranking.csv"
"/home/claude/E1_live/e2_final.json"
"/home/claude/E1_live/bl2_metadata.json"   # compute_e4_live.py only

# e4_rubric/rubric_judgment_scores.py (__main__ block only, not the JUDGMENT data itself)
"/home/claude/fullwriteup/stage4_input_items_live.json"
```

None of these have an inline "HARDCODED PATH NOTICE" docstring comment yet (unlike Stage 2's and Stage 3's scripts, which received that treatment in earlier verification passes) — this is a real, disclosed gap in this folder specifically. All seven scripts will fail immediately on another machine until these lines are edited to point at:

- Stage 2's `cluster_assignments.csv` and the review corpus batch file (your `stage2_clustering/clusters/` and `.../batches/`)
- Stage 3's `stage3_roadmap_items.json` and `prep/` folder (your `stage3_summarization/`)
- This folder's own `bl1_ClsuterScore/bl1_ranking.csv`, `bl2_random_forest/e2_final.json`, and `bl2_random_forest/bl2_metadata.json` (all present here, just under different absolute paths than these scripts expect)

`candidate_matching.py`'s `E1_CSV` path and the `e4_rubric/` merge/verify scripts that don't appear in the list above use only paths relative to their own folder (`HERE = os.path.dirname(...)`), so they run correctly wherever this folder is placed.

---

## 6. End-to-end reproduction steps

### 6.1 One-time setup
- Install Python 3.11+, `scikit-learn`, `imbalanced-learn`, `scipy`.
- Edit the hardcoded paths in §5.
- Ensure Stage 2 and Stage 3 have already been run (or their output files are otherwise available).

### 6.2 BL1 (`bl1_ClsuterScore/`)
- Run `compute_cluster_features.py` — joins Stage 2's cluster assignments to the corpus, computes `bl1_cluster_score` for all non-noise clusters using each cluster's full member population (not Stage 3's 150-review sample).
- Run `verify_bl1_independent.py` — re-derives the score from raw files independently; expect `PASSED` with 0 mismatches.

### 6.3 E1 (`bl2_random_forest/build_e1.py`)
- Requires live web access. Fetches Trading 212's Discourse "What's New" category (paginated to exhaustion), Robinhood's newsroom/sitemap plus targeted article searches, and Coinbase's blog listing pages plus targeted article searches.
- Sets an `in_corpus_window` flag per row based on the review corpus's actual date range (confirm this range directly from the corpus before hardcoding the window, as this run did).
- Output: `e1_release_notes.csv`.

### 6.4 E2 (`bl2_random_forest/candidate_matching.py` → `review_e2_matches.py`)
- `candidate_matching.py`: TF-IDF + cosine similarity between the 77 roadmap items and the in-window E1 notes, same-app-preferred ranking (via each cluster's dominant app, read from Stage 3's `prep/` files), top-3 per cluster.
- `review_e2_matches.py`: for the highest-scoring candidates, fetch the real article content and make a content-grounded match/no-match call — never accept a lexical score alone as evidence of a match. Disclose explicitly that this is AI-only, not independent human review.
- Output: `e2_candidates.json`, `e2_human_labels.csv`, `e2_final.csv`/`.json`.

### 6.5 BL2 (`bl2_random_forest/compute_bl2_features.py` → `train_bl2.py`)
- Compute the 4 features per cluster (`delta_rating_app`'s exact formula, reconstructed from prose in this run, is documented in `BL2_LIVE_RUN_LOG.md` §7).
- Train via LOOCV. If E2 finds 0 positives (as this run did), report accuracy/confusion-matrix for transparency only and disclose that precision/recall/F1/ROC-AUC are undefined, not zero — do not silently skip this reporting.

### 6.6 Rubric (`e4_rubric/`)
- Compute 5 deterministic dimensions (reach, severity, engagement, recency, cross-platform generality — exact formulas in `Rubric_LIVE_RUN_LOG.md` §2).
- Genuinely, individually judge actionability and overall_priority per cluster by reading its real title/description/quotes (`rubric_judgment_scores.py`).
- Merge (`build_stage4_rubric.py`) and independently verify the merge (`verify_stage4_rubric_merge_live.py`).

### 6.7 E4 (`e4_rubric/compute_e4_live.py`)
- Join rubric/BL1/E2(/BL2) outputs on `(category, cluster_id)`.
- Compute Precision@k, MRR, Spearman vs. E2 ground truth for each method — report `None` with an explanatory note if there are 0 positive examples, never a misleading `0.0`.
- Compute pairwise Spearman between methods' own rankings; exclude any method whose output has zero variance (as BL2's does whenever E2 finds 0 positives) from pairwise comparisons, with the reason disclosed.
- Independently re-verify (`verify_e4_independent_live.py`).

---

## 7. Exact configuration used

| Setting | Value |
|---|---|
| BL1 weights (w_rev, w_th, w_ra) | 1, 0.1, 1 (Wei et al.'s published defaults, unmodified) |
| BL2 model | RandomForestClassifier, 100 trees, `max_features="sqrt"`, unlimited depth, `random_state=42` |
| BL2 CV | Leave-One-Out (not 10-fold — too few clusters/positives for meaningful folds) |
| BL2 features | `n_reviews`, `avg_rating`, `delta_rating_app`, `n_distinct_app_versions` |
| E1 collection window | 2024-06-01 to 2026-09-24 (the review corpus's own confirmed date range) |
| E2 matching | `TfidfVectorizer(stop_words="english", max_features=5000)`, cosine similarity, same-app-preferred, top-3 per cluster |
| Rubric scale | 1–10 per dimension and for `overall_priority` |
| Model (E2 review, rubric judgment) | Claude Sonnet 5 (`claude-sonnet-5`), used directly within this session |

### On "the exact prompt" — same disclosed gap as Stage 3

E2's match-review judgments and the rubric's actionability/overall_priority judgments were made directly within this session, reading each candidate's or cluster's real content. **The literal, word-for-word instructions given for each judgment are not preserved as a file artifact.** What survives is the judgment *output* itself — `review_e2_matches.py`'s `DETAILED_REASONS` dict (10 individually-reasoned verdicts) and `rubric_judgment_scores.py`'s `JUDGMENT` dict (all 77 clusters) — plus a paraphrased description of the criteria applied, in each run log. This is the same category of gap disclosed for Stage 3's generation/rating subagent prompts.

---

## 8. A prompt you can hand an AI assistant to run this stage for you

```
Run Stage 4 (roadmap prioritization) of the review-mining pipeline.
Input: Stage 3's 77 structured roadmap items (title, description, quotes,
n_total) and Stage 2's cluster assignments + review corpus.

1. BL1 (rule-based baseline). Compute ClusterScore = (w_rev*|reviews| +
   w_th*|thumbsup|) / (w_ra*rating) per cluster, using each cluster's FULL
   member population (not a sampled subset), with Wei et al. (2023)'s
   published default weights (1, 0.1, 1) unmodified. Independently
   re-derive every score from the raw corpus/assignment files in a
   separate script -- do not trust the first script's own stored,
   rounded output.

2. E1 (live release-note collection). For each app in the corpus, fetch
   real, dated release notes/changelog entries from the company's own
   real public source (forum API, newsroom, blog). Confirm the review
   corpus's own date range directly from the data, and flag each release
   note as in-window or out-of-window against that range -- do not invent
   or backfill dates. Disclose explicitly, per app, whether the
   collection is exhaustive or not, and why.

3. E2 (candidate matching + review). TF-IDF + cosine similarity between
   each cluster's (title + description) and each in-window release
   note's (title + description), preferring same-app candidates where a
   cluster's dominant app is determinable. For the highest-scoring
   candidates, fetch the real article content and make a match/no-match
   call grounded in that content -- a match counts only if the release
   specifically addresses the cluster's actual complaint or request, not
   just topical/keyword overlap. Disclose explicitly that this is not an
   independent blind human review.

4. BL2 (trained baseline). Train a Random Forest (100 trees, sqrt
   features, unlimited depth) via Leave-One-Out CV on n_reviews,
   avg_rating, a rating-delta-vs-app-baseline feature, and a
   version-diversity feature, to predict E2's match label. If the
   positive class has too few (or zero) examples, report that
   honestly -- do not report a misleadingly high accuracy without the
   caveat that it reflects a degenerate label distribution, not model
   skill, and report undefined (not zero) for any metric that requires a
   positive example to compute.

5. Rubric (LLM-applied prioritization). Score reach, severity,
   engagement, recency, and cross-platform generality via disclosed,
   deterministic formulas from already-computed data. Genuinely,
   individually judge actionability and a holistic overall_priority
   (1-10) per cluster by reading its real title, description, and sample
   quotes -- not a formula. Independently verify the merge of
   deterministic + judged fields against both sources.

6. E4 (rank-agreement evaluation). Join rubric/BL1/BL2 scores against
   E2's match label on (category, cluster_id). Compute Precision@k, MRR,
   and Spearman correlation of each method vs. the ground truth, and
   pairwise Spearman between methods' own rankings. If the ground truth
   has zero positive examples, report every ground-truth-dependent metric
   as explicitly undefined, not a misleading 0.0 -- and exclude any
   method whose output has zero variance from pairwise comparisons, with
   the reason disclosed. Independently re-verify every number from the
   three raw source files directly.

7. Write it up with full source verification. Every quantitative claim
   traceable to an exact command or file. State plainly which judgments
   are AI-only (E2's match review, the rubric's actionability/overall_
   priority) versus purely deterministic (BL1's arithmetic, the rubric's
   other 5 dimensions). Disclose every adaptation from the cited papers'
   original methodology (feature substitutions, CV scheme, the rubric's
   deterministic dimensions) and why each was necessary. Do not invent or
   backfill any release-note content, date, or judgment.

After finishing, report back: BL1's score distribution and top/bottom
clusters; E1's per-app collection counts and exhaustiveness disclosure;
E2's match count and the specific reasoning for each individually-reviewed
candidate; BL2's training outcome including whether any metric was
undefined; the rubric's score distribution and top/floor clusters; E4's
full results including which comparisons were undefined and why; and
every limitation, including that this project's E1/E2 data has so far
found zero genuine cluster-to-release matches across all release notes
checked (not just the in-window subset), so no method has yet been
validated against real ground truth on this project's data.
```

---

## 9. Known gaps and disclosed limitations

- **Citation year ambiguity for BL2's source paper.** Scalabrino et al.'s DOI (`10.1109/TSE.2017.2759112`) and the paper's own PDF give 2017; the lead author's own publication list and earlier drafts of this thesis's text give 2019. This is plausibly an online-first-vs-print-issue year discrepancy rather than a wrong citation, but it has not been resolved to a single authoritative year — a decision for the thesis author, not silently picked here. The tool name is independently confirmed via web search as "CLAP" (Crowd Listener for releAse Planning).
- **`e1_release_note_scraper/` is not the E1 source that actually fed BL2/E4.** It is a separate, more elaborate scraper whose own README discloses that live company-page crawling "remains unverified in this execution environment," and whose shipped example output (23 rows) is a different size/shape from the 147-row dataset `build_e1.py` actually produced. Both tools are real; only `build_e1.py`'s output is what downstream numbers trace back to.
- **Hardcoded, non-portable paths** in 6 of the pipeline's scripts (§5) — unlike Stage 2/3, these have not yet received an inline "HARDCODED PATH NOTICE" docstring comment. Manual editing is required before any of these scripts will run on a different machine.
- **No literal, verbatim record of the exact instructions given for E2's match review or the rubric's judgment step** (§7) — only the judgment outputs and a paraphrased criteria description survive, the same category of gap already disclosed for Stage 3.
- **E1 is not fully exhaustive for Robinhood and Coinbase** — only Trading 212's collection is confirmed exhaustive (its API was paginated to an empty page).
- **E2's match review, and the rubric's actionability/overall_priority judgment, are AI-only** — not independently blind-reviewed by a human, disclosed per-row/per-cluster.
- **The zero-positive E2 outcome makes BL2 untestable, and most of E4 uncomputable, on this project's current data** — not a weak result but an absent one for every ground-truth-dependent metric. This is a genuine finding about this project's real data, not an error in any script.
- **The supplementary full-corpus check (§3.3) was not saved as a file in this folder.** It re-used the same methodology and confirmed the same 0-match conclusion holds across all 147 release notes, not just the 85 in-window ones, but it exists only as a reported finding in this document and the conversation that produced it — not as a standalone artifact with its own run log, unlike every other step in this pipeline. If this finding is to be cited in the thesis as a completed check, it should be re-run and logged as its own artifact first, consistent with how every other number in this package is backed by a file.
- **Non-determinism carries through from Stage 2.** BL1's, BL2's, and the rubric's per-cluster numbers are all downstream of Stage 2's non-deterministic clustering — a different Stage 2 rerun would be expected to produce different cluster-level values throughout Stage 4, even though every Stage 4 computation itself is deterministic (BL1, BL2 training, the rubric's 5 formula-based dimensions) or independently verified (E2, the rubric merge, E4).

---

## 10. Thesis-text cross-check: two open items

Independently checking the pasted §5.4 thesis text against this folder's verified data (§3 above) confirmed the great majority of claims match exactly — E1's 147-note collection and per-app counts, E2's 0/77 match result and the specific rejected-candidate reasoning, BL2's degenerate training outcome, the rubric's distribution and its 6 priority-10 clusters (matching Table 5.10 exactly), and E4's rubric-vs-BL1 rho of 0.408. Two items remain open, both requiring a decision in the thesis text itself rather than in this folder:

1. **§5.4.4's "unrestricted historical check" claim is not accurate to what `candidate_matching.py` actually executes** — the script filters to `in_corpus_window == "True"` (85 of 147 notes) before any matching, by design (matching release notes that predate the review corpus would credit pre-existing features as if they were fixes). The supplementary check in §3.3 above confirms an unrestricted check would not have changed the conclusion, but that check itself isn't yet a logged artifact (see §9). Until it is, the thesis text should describe what was actually run: a deliberately in-window-restricted check, not an unrestricted one.
2. **§5.4.8's "an earlier execution produced 65 [clusters]" sentence** references the prior run's cluster count for context. Given this folder's own docs/scripts have now had all old-run comparisons removed, this sentence is a candidate for the same treatment in the thesis text, for consistency — left as the thesis author's call, not changed here.

---

## 11. Verification note

*Everything above marked "✅ verified this session" was checked by directly opening and recomputing from the actual files in `stage4_prioritization/` as connected to this session on 2026-09-30 — cluster scores, E1/E2 counts, BL2 training labels, the rubric's distribution, and E4's pairwise correlation were computed fresh from `cluster_features.json`, `e1_release_notes.csv`, `e2_final.csv`, `bl2_metadata.json`, `stage4_scores_merged_live.json`, and `e4_results_live.json` themselves, not copied from the folder's own README or log claims.*
