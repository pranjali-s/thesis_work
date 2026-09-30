# BL2 Live Run Log — Random Forest Classifier Baseline

**Run date:** 2026-09-24
**Scope:** Full re-derivation of BL2 (trained classifier baseline) against this session's live 77-cluster Stage 2/3 output, including a live re-collection of E1 (real release notes) and a fresh E2 (cluster-to-release matching) pass.

---

## 1. What BL2 is

BL2 is a trained-classifier baseline adapted from Scalabrino et al. (2017, IEEE Transactions on Software Engineering, "Listening to the Crowd for the Release Planning of Mobile Apps," DOI 10.1109/TSE.2017.2759112). The original paper trains a 100-tree Random Forest (Weka, `sqrt` random attributes per split, unlimited depth) on four features — `|reviews|`, average rating, delta-rating-vs-app-baseline, and `|devices|` — to predict whether a cluster of review complaints/requests was addressed in a later app release, evaluated via 10-fold cross-validation on a 207-cluster, human-labeled ground truth (27 positive, ~13%), reporting AUROC 0.775.

This project adapts BL2 rather than reproducing it verbatim, for reasons documented previously in `Stage4_BL2_writeup.md` and unchanged this run:

- **`|devices|` → `n_distinct_app_versions`**: the original paper counts distinct device models per cluster (from Google Play device data this project has no access to); this project substitutes the count of distinct `app_version` strings among a cluster's member reviews, with missing values excluded and tracked.
- **Ground truth is this project's own E2 output**, not the original paper's 207-cluster dataset (which is not public). The label is `e2_matched`: whether a cluster's roadmap item was judged to have a genuine, content-verified match among real release notes.
- **Leave-One-Out CV instead of 10-fold CV**: with only 77 clusters and (this run) zero positive examples, 10-fold CV would not produce meaningful, comparably-sized folds; LOOCV is used instead.
- **SMOTE oversampling** is applied only where the positive class has enough members for a meaningful `k_neighbors`; it is never treated as the headline result when positives are too few (this project's standing practice, reconfirmed below).

## 2. Why this run required E1 and E2 to be live-recollected, not just BL2

Stage 2 (embedding + clustering), Stage 3 (roadmap generation), and BL1 (rule-based ClusterScore) were all rerun earlier in this session using deterministic, documented code re-derived from this project's own detailed specs (`Stage2_redo_package_README.md`, `Stage4_BL1_writeup.md`, etc.) — safe to reconstruct because the *methodology* was fully specified even though the original scripts weren't in this session's workspace.

E1 is different: it is a snapshot of **real, dated, external release-note content** (Trading 212 community posts, Robinhood newsroom articles, Coinbase blog posts). The original 156-row E1 dataset and the original E2 matching-and-review outputs were not recoverable from this workspace or from the Project's saved docs (`E1_status.md` and `E2_status.md` contain only prose summaries, not raw data). Reconstructing E1 "from memory" would mean fabricating plausible-looking release notes and dates — exactly the kind of fabrication this project's standing transparency requirement forbids. Given this, three options were put to the user directly (via a clarifying question): skip BL2 entirely, reconstruct E1 with an explicit synthetic-data warning, or re-fetch E1 live from the same real sources and rerun E2 fresh. **The user chose the live re-fetch.** Everything below reflects that live re-collection.

## 3. Environment

- Python 3.11.15
- scikit-learn 1.8.0
- imbalanced-learn 0.14.2 (freshly installed this session: `pip install imbalanced-learn --break-system-packages -q`; version matches what the original write-up documented)
- Inputs: `/home/claude/Stage2_live/clusters/cluster_assignments.csv`, `/home/claude/Stage2_live/batches/batch_001.csv` (52,392-review corpus), `/home/claude/Stage3_live/stage3_roadmap_items.json` (77 roadmap items), `/home/claude/BL1_live/cluster_features.json` (verified 77/77 against independent recomputation, see `BL1_LIVE_RUN_LOG.md`)
- Review corpus date range confirmed by direct query: **2024-08-15 to 2026-08-15**, apps = {Robinhood, Coinbase, Trading 212}
- E1 collection window set to **2024-06-01 to 2026-09-24** (comfortably covers the corpus window plus a margin for release notes that could plausibly predate or postdate reviews referencing them)

## 4. Step 1 — E1: live release-note collection

**Script:** `build_e1.py`. Console output (this run):

```
Wrote 147 rows to /home/claude/E1_live/e1_release_notes.csv
  Trading 212: 94 total, 34 within corpus window [2024-06-01, 2026-09-24]
  Robinhood: 16 total, 14 within corpus window [2024-06-01, 2026-09-24]
  Coinbase: 37 total, 37 within corpus window [2024-06-01, 2026-09-24]
```

**Per-app methodology and honesty notes:**

- **Trading 212 (94 total, 34 in-window)** — fetched via the real Discourse JSON API (`community.trading212.com/c/whats-new.json?page=N`), 4 paginated fetches, page 4 confirmed empty (i.e., exhaustive — this is the complete "What's New" category as of the fetch date). Direct `curl` to this endpoint was blocked by the environment's agent proxy (`HTTP 403` on the CONNECT tunnel); `WebFetch` succeeded where raw `curl` could not.
- **Robinhood (16 total, 14 in-window)** — the newsroom listing page uses client-side JS pagination (`?page=2` returned the identical list as `?page=1`), so the sitemap route was tried instead: `blog.robinhood.com/sitemap.xml` returned 404; `robinhood.com/sitemap.xml` (a sitemap index) led to `robinhood.com/us/en/sitemap-newsroom.xml`, which listed 400+ URLs but all sharing a uniform crawl-date `lastmod` (not real publish dates). Individual articles were fetched via WebFetch/WebSearch to recover real per-article dates and descriptions. **This collection is explicitly NOT exhaustive** — it is 10 items from the newsroom listing plus 6 individually-searched-and-fetched items, not a complete crawl of Robinhood's release history.
- **Coinbase (37 total, 37 in-window)** — both `blog.coinbase.com/sitemap/sitemap.xml` and `www.coinbase.com/sitemap-cms.xml` failed (`ROBOTS_DISALLOWED` / `403`), so the human-readable blog listing pages (`www.coinbase.com/blog`, `www.coinbase.com/blog/landing/product`) were fetched directly instead, plus 2 individually-fetched feature-relevant articles found via WebSearch. **Also explicitly NOT exhaustive** — it reflects the current blog listing pages, not a full historical crawl.

**Bottom line on E1 completeness:** Trading 212 is confirmed exhaustive. Robinhood and Coinbase are real, dated, genuine content but not exhaustive collections.

## 5. Step 2a — E2 candidate matching (TF-IDF + cosine similarity)

**Script:** `candidate_matching.py`. Console output:

```
77 Stage 3 roadmap items, 85 in-window E1 release notes.
Wrote e2_candidates.json -- 77 clusters x top-3 candidates.
Candidate similarity scores: min=0.0000 median=0.0598 max=0.2641
```

Method: `TfidfVectorizer(stop_words="english", max_features=5000)` fit jointly over all 77 cluster texts (title + description) and 85 in-window E1 texts (title + description); cosine similarity computed between every (cluster, E1 row) pair; candidates ranked with same-app rows preferred first (not hard-excluded cross-app), top-3 kept per cluster regardless of score.

Top-1 candidate scores across all 77 clusters, highest 15: 0.2641, 0.2234, 0.2225, 0.2120, 0.1513, 0.1465, 0.1406, 0.1354, 0.1348, 0.1340, 0.1322, 0.1320, 0.1310, 0.1259, 0.1257 — i.e., even the single best-scoring cluster tops out at 0.26 cosine similarity, and the scores fall off quickly.

## 6. Step 2b — E2 match review (conservative, content-grounded)

**Script:** `review_e2_matches.py`. Console output:

```
Reviewed 77 clusters. Matched: 0. Not matched: 77.
Individually content-verified (fetched real article text): 10 clusters (the highest-scoring / most plausible candidates).
Remaining clusters: no in-window candidate scored highly enough to warrant an individual content fetch; verdict based on title/description comparison against the candidate list.
```

**Disclosed methodology:** this step was not an independent, blind human review. Claude made the match/no-match call directly, grounded in each candidate's real fetched content: a match counts only if the release genuinely, specifically addresses the cluster's actual complaint or request, not just topical/keyword overlap. Every output row carries this disclosure verbatim. This remains a deviation from Scalabrino et al.'s independent-human-review standard.

**The 10 individually content-verified candidates** (highest-scoring / most plausible; full real article text fetched and read for each) — all rejected on specific grounds:

| Cluster | Top candidate | Why rejected |
|---|---|---|
| CHARTING_TOOLS/0 | "Portfolio Redesign Update" (Trading 212) | Announces *reverting* a redesign after complaints — doesn't address chart/graph display bugs, the cluster's actual complaint |
| CUSTOMER_SUPPORT/1 | "Autopilot: engineering an agentic quality loop for support automation" (Coinbase) | Internal engineering/testing-infrastructure post; no stated effect on customer queue times or bot-gating |
| FEES_SUBSCRIPTION/1 | "We're lowering fees for many active traders on Coinbase Advanced" (Coinbase) | Fee cut scoped only to the separate "Coinbase Advanced" product, not the standard retail app the cluster complains about |
| SECURITY_PRIVACY/1 | "How We Are Making Coinbase Easier to Use" (Coinbase) | New 2FA/Time-Delay features don't address the cluster's specific complaints (balance-flash-before-lock, missing auto-logout/passkey) |
| SECURITY_PRIVACY/0 | (same article) | Cluster is general positive sentiment, no specific gap to match against |
| ASSET_COVERAGE/3 | "The Trading 212 SIPP is now live for everyone in the UK" | Pension product launch, unrelated to country-of-residence sign-up blocking |
| PREDICTION_MARKETS/2 | Robinhood/Crypto.com/OG.com partnership | Expands access, doesn't address forced-placement/no-opt-out complaint |
| CRYPTO_SPECIFIC/4 | "Canadians Can Now Earn up to 4.5% Rewards on Their USDC Balance" | Keyword overlap only; different mechanism (USDC interest vs. existing Learn-and-Earn program); cluster is positive sentiment, not a gap |
| CRYPTO_SPECIFIC/3 | (same article) | Same reasoning — not applicable |
| FEES_SUBSCRIPTION/4 | "The next wave of Coinbase One onchain benefits" | New subscription benefits, doesn't address unauthorized/hidden-fee complaints |

The remaining 67 clusters had top candidate scores too low (mostly below ~0.13) to warrant an individual full-article fetch; their no-match verdicts were reached from title/description comparison against the candidate list, each with a disclosed reason recorded in `e2_human_labels.csv`.

**Result: 0/77 matched (0.0%).** Release notes are overwhelmingly PR-oriented (feature launches, partnerships, rate changes) and rarely map cleanly onto specific review-level complaints, in this run's data.

## 7. Step 3 — BL2 feature computation

**Script:** `compute_bl2_features.py`. Console output:

```
App baseline ratings (full corpus): {'Robinhood': 3.6351, 'Coinbase': 3.6399, 'Trading 212': 3.8941}
Wrote 77 clusters to /home/claude/E1_live/cluster_features_bl2.json
n_distinct_app_versions range: 17-445
Total missing app_version among cluster members: 8039/58388 (13.77%)
```

**`delta_rating_app` formula disclosure:** the original write-up (`Stage4_BL1_writeup.md` §4.4.4.8) describes this feature only in prose — "cluster average rating minus that cluster's app-weighted baseline rating" — without a byte-for-byte formula to recover. This run implements that prose description directly, rather than guessing silently:

```
app_baseline_rating[app] = mean(rating) over ALL reviews of that app in the full corpus
cluster's app-weighted baseline = Σ(app_baseline_rating[a] × count_in_cluster[a]) / n_reviews_in_cluster
delta_rating_app = cluster's own avg_rating − that weighted baseline
```

Resulting `delta_rating_app` ranges from **−2.5697 to +1.2817** across the 77 clusters (negative = cluster rated worse than a typical review of the same app(s); positive = better). `n_distinct_app_versions` ranges from **17 to 445**. Missing `app_version` among cluster members is 8,039/58,388 (13.77%), closely matching the corpus-wide missing rate of 13.79% (7,227/52,392) — i.e., missingness is roughly uniform across clusters, not concentrated.

## 8. Step 4 — BL2 training (Random Forest, LOOCV)

**Script:** `train_bl2.py`. Full console output (this run):

```
Joined 77 clusters on (category, cluster_id) -- exact key match confirmed.
Target label e2_matched: 0 positive / 77 negative out of 77 (0.0% positive).

ZERO positive examples in this run's E2 ground truth.
A classifier cannot learn a positive-class decision boundary from zero positive examples -- this is not a training failure, it is a direct, mechanical consequence of the label distribution. Precision/recall/F1 for the positive class and ROC-AUC are UNDEFINED (not zero, not computable) with no positive examples to score against.
Running LOOCV anyway to report accuracy / confusion matrix for transparency, and to confirm the model does exactly what a 0-positive label set implies: predicts negative for every held-out cluster.
LOOCV accuracy: 1.0000 (trivially 1.0 if the model predicts 0 for every cluster, which is the only thing it CAN learn from an all-negative training set)
Confusion matrix [[TN FP][FN TP]]: [[77, 0], [0, 0]]
Feature importances (single fit, all-negative target -- not meaningful, reported for transparency only): {'n_reviews': 0.0, 'avg_rating': 0.0, 'delta_rating_app': 0.0, 'n_distinct_app_versions': 0.0}

Wrote bl2_metadata.json and bl2_predictions.csv
```

**How to read these numbers — explicitly, so the 1.0000 accuracy is not mistaken for a good result:**

- With zero positive examples, every LOOCV training fold is 100% negative. A Random Forest trained on an all-negative set can only ever learn to predict "negative." Predicting negative for a held-out cluster that is (by construction, this run) also negative is correct by definition — hence accuracy = 1.0000. This number reflects the degenerate label distribution, not classifier skill.
- **Precision, recall, F1, and ROC-AUC for the positive class are UNDEFINED**, not zero and not computable — there is no positive example anywhere to score a prediction against.
- **SMOTE cannot run at all this run.** SMOTE synthesizes new minority-class examples by interpolating between existing minority-class neighbors (`k_neighbors`), which requires at least one real minority (positive) example to interpolate from. With 0 positives, there is nothing to interpolate from, so no SMOTE variant exists this run (`variants.smote_k1` in `bl2_metadata.json` is a note, not a metric).
- Feature importances from the single full-data fit are also degenerate (all zero) — a Random Forest fit on a target with a single class has nothing to split on to reduce impurity, so every feature reports zero importance. Reported here for structural transparency only, not as a finding.

**Headline finding, in `bl2_metadata.json`:**

> "BL2 cannot be trained meaningfully at all on this run's E2 ground truth — there is no positive class whatsoever (0/77). A classifier cannot learn a positive-class decision boundary with zero positive examples to learn from."

## 9. Limitations (this run, in addition to those already disclosed for BL1/Stage 2/Stage 3)

- **E1 is not fully exhaustive for Robinhood and Coinbase.** A more exhaustive crawl (e.g., a working sitemap, or an official changelog API if either company offers one) could in principle surface additional release notes, including ones that might genuinely match a cluster. Trading 212 is the one source confirmed exhaustive in this run.
- **E2's match review is AI-only, not independently blind-reviewed**, as disclosed per-row — a deviation from Scalabrino et al.'s methodology.
- **The zero-positive outcome makes BL2 untestable this run.** No AUROC, precision, recall, or F1 exists to report.
- **Non-determinism carries through from Stage 2.** As with BL1, this run's BL2 features derive from Stage 2's live 77-cluster output; Stage 2's clustering is itself non-deterministic (documented in `Stage2_LIVE_RUN_LOG.md`), so a different Stage 2 rerun would be expected to produce different cluster-level BL2 feature values.
- **`delta_rating_app`'s exact formula was reconstructed from prose** describing the feature conceptually, not recovered byte-for-byte from a preserved implementation (documented in Section 7); it is believed faithful to the described definition but this could not be checked against any other numerical output.

## 10. Package contents

- `BL2_LIVE_RUN_LOG.md` — this document
- `e1_release_notes.csv` — 147 real, dated release notes (94 Trading 212 / 16 Robinhood / 37 Coinbase), with `in_corpus_window` flag
- `e2_candidates.json` — top-3 TF-IDF/cosine candidates per cluster (77 × 3)
- `e2_human_labels.csv` — full per-cluster match/no-match verdicts with disclosed reasoning
- `e2_final.csv`, `e2_final.json` — compiled E2 ground truth (77 clusters, `e2_matched` label)
- `cluster_features_bl2.json` — 77-cluster BL2 feature set (n_reviews, avg_rating, delta_rating_app, n_distinct_app_versions, plus supporting fields)
- `bl2_metadata.json` — training results, feature importances, headline finding
- `bl2_predictions.csv` — per-cluster features + label in flat CSV form
- Scripts: `build_e1.py`, `candidate_matching.py`, `review_e2_matches.py`, `compute_bl2_features.py`, `train_bl2.py`
- Console logs: `build_e1_stdout.log`, `candidate_matching_stdout.log`, `review_e2_matches_stdout.log`, `compute_bl2_features_stdout.log`, `train_bl2_stdout.log`
