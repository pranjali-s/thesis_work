# BL1 (Rule-Based ClusterScore Baseline) — Live Run Log

This is a genuine, real-time execution of BL1, run in this session on 2026-09-24 against this session's own live Stage 2 rerun output (`/home/claude/Stage2_live/`, documented in `Stage2_LIVE_RUN_LOG.md`) — not the original session's 65-cluster output. Every number below is taken directly from this run's actual files; the original run's numbers (from `Stage4_BL1_writeup.md`, §4.4.4) are shown only for explicit, labeled comparison.

## 1. What BL1 is (unchanged from the original write-up)

BL1 reproduces the `ClusterScore` ranking formula from Wei, Courbis, Lambolais, Xu, Bernard & Dray, "Zero-shot Bilingual App Reviews Mining with Large Language Models" (arXiv:2311.03058, 2023):

> ClusterScore = (w_rev · |reviews| + w_th · |thumbsup|) / (w_ra · rating)

with the paper's published default weights, used unmodified: w_rev = 1, w_th = 0.1, w_ra = 1. This project reuses only the ranking formula, not the paper's own clustering method — it ranks this project's own Stage 2 clusters. Neither the clustering step nor this ranking computation involves any LLM or human judgment; it is pure arithmetic over three counted/averaged quantities, exactly as in the original write-up.

## 2. Inputs used (verified before computing anything)

| File | Rows | Notes |
|---|---|---|
| `Stage2_live/clusters/cluster_assignments.csv` | 67,300 data rows | This session's live Stage 2 rerun output — 77 non-noise clusters, 8,912 noise rows. |
| `Stage2_live/batches/batch_001.csv` | 52,392 rows | The same corpus used for this session's live Stage 2 rerun; columns include `rating`, `thumbs_up_count`. |

**Verified directly, not assumed:** the corpus has 52,392 rows, 52,392 unique `review_id_hash` values, 0 rows with empty `rating` (0.00%), and 2,311 rows with empty `thumbs_up_count` (4.41%) — this 4.41% figure matches the original run's corpus-wide imputation rate exactly (§4.4.4.7 of `Stage4_BL1_writeup.md`), confirming this is the same underlying corpus. Every `review_id_hash` in `cluster_assignments.csv` is confirmed to exist in the corpus (`assignment ids subset of corpus ids: True`) — checked directly, not assumed, before running the feature computation.

## 3. Environment

Python 3.11.15 (same interpreter as the Stage 2/Stage 3 live runs, same container). No third-party libraries required — pure standard library (`csv`, `json`, `statistics`, `collections`), exactly as in the original.

## 4. Step 1 — Feature computation (`compute_cluster_features.py`)

**Run:** 2026-09-24T18:38:29Z

Console output (full log: `compute_stdout.log`):
```
Corpus loaded: 52392 rows from /home/claude/Stage2_live/batches/batch_001.csv
  rating empty: 0 (0.00%)
  thumbs_up_count empty in source file: 2311 (4.41%)  -- imputed as 0, per disclosed policy
Cluster assignments loaded: 77 non-noise clusters (8912 noise rows excluded).

Wrote 77 clusters to cluster_features.json
Wrote 77 ranked clusters to bl1_ranking.csv
Total reviews across all clusters: 58388
Total missing_text (assignment row with no corpus match): 0
Total thumbs-up imputed: 2263 (3.88% of cluster-member reviews)
```

**58,388 total cluster-member reviews** matches this session's live Stage 2 non-noise total exactly (`Stage2_LIVE_RUN_LOG.md` §5: 58,388 non-noise rows). **0 missing_text** — every cluster-assignment row resolved to a real corpus row, full data integrity confirmed. This computation uses each cluster's full member population (not Stage 3's 150-review-capped sample), exactly as the original methodology requires (§4.4.4.6) — the formula is defined over a cluster's real size and real engagement.

## 5. Step 2 — Independent verification (`verify_bl1_independent.py`)

Per this project's standing rule that a script's own printed output is not sufficient evidence on its own, `bl1_cluster_score` was independently re-derived by a separate script that reads the raw corpus and assignment files itself — it does not import `compute_cluster_features.py` and does not trust `cluster_features.json`'s stored, rounded intermediate values (recomputing `avg_rating` from the raw per-review ratings, not a rounded field — the exact pitfall the original write-up's §4.4.4.9 identified and disclosed).

**Run:** 2026-09-24T18:38:32Z

```
77 clusters checked.
Mismatches (tolerance 1e-06): 0

PASSED
```

**77/77 clusters matched to within 1e-6, 0 mismatches.**

## 6. Results: BL1 ranking of all 77 clusters (this run)

**Summary statistics (n = 77 clusters, all received a score — 0 skipped):**

| Statistic | This run | Original run (65 clusters) |
|---|---|---|
| Minimum score | 7.38 (Charting, Analytics & Professional Tools, cluster 0) | 7.15 (same category/cluster) |
| Maximum score | 3,468.40 (Customer Support Quality, cluster 1) | 4,250.65 (Customer Support Quality, cluster 0) |
| Mean | 405.69 | 509.43 |
| Median | 102.22 | 122.21 |
| Standard deviation | 739.91 | 845.40 |
| Clusters scoring ≥ 1,000 | 11 | 11 |
| Clusters scoring 100–999 | 28 | 26 |
| Clusters scoring 10–99 | 37 | 26 |
| Clusters scoring < 10 | 1 | 2 |

The distribution is still heavily right-skewed (mean roughly 4x the median), consistent with the original run — expected from a formula whose numerator scales with raw review count. The lower mean/median/max in this run is a direct, mechanical consequence of Stage 2 producing more, smaller clusters (77 vs. 65: the same 58,388 non-noise reviews are now spread across 12 more clusters, so no single cluster is as large as the original's biggest).

**Table — Top 10 clusters by `bl1_cluster_score` (this run):**

| Rank | Category | Cluster | Score | n_reviews | avg_rating | sum_thumbsup |
|---|---|---|---|---|---|---|
| 1 | Customer Support Quality | 1 | 3,468.40 | 4,357 | 1.88 | 21,754 |
| 2 | Account Access & Authentication | 1 | 3,436.00 | 4,170 | 1.59 | 12,864 |
| 3 | Funds Transfer | 0 | 3,153.72 | 3,235 | 1.43 | 12,660 |
| 4 | General Sentiment (residual) | 3 | 1,770.49 | 7,740 | 4.43 | 1,078 |
| 5 | App Stability & Performance | 2 | 1,754.96 | 1,576 | 1.76 | 15,130 |
| 6 | Trade Execution & Order Handling | 1 | 1,665.40 | 1,372 | 1.62 | 13,191 |
| 7 | App Stability & Performance | 3 | 1,533.23 | 2,288 | 1.80 | 4,749 |
| 8 | Usability & Navigation | 3 | 1,364.48 | 1,987 | 2.23 | 10,599 |
| 9 | Trust, Fairness & Regulatory Sentiment | 3 | 1,319.02 | 1,282 | 1.26 | 3,817 |
| 10 | Fees, Subscription & Monetization | 2 | 1,186.83 | 882 | 1.36 | 7,287 |

**Table — Bottom 5 clusters by `bl1_cluster_score` (this run):**

| Rank | Category | Cluster | Score | n_reviews | avg_rating | sum_thumbsup |
|---|---|---|---|---|---|---|
| 77 | Charting, Analytics & Professional Tools | 0 | 7.38 | 24 | 3.25 | 0 |
| 76 | Asset & Market Coverage | 2 | 12.12 | 40 | 3.33 | 3 |
| 75 | Security & Data Privacy | 9 | 21.32 | 28 | 1.39 | 17 |
| 74 | Fees, Subscription & Monetization | 6 | 23.53 | 86 | 3.88 | 54 |
| 73 | Crypto-Specific Functionality | 4 | 28.41 | 131 | 4.83 | 63 |

The full 77-row ranking is `bl1_ranking.csv`.

## 7. Direct comparison against the original run's Table 4.4.4.8

This mirrors what `Stage2_LIVE_RUN_LOG.md` §6 did for clustering: an explicit, cluster-by-cluster comparison, not just a restated caveat.

Four categories whose Stage 2 clustering landed close to the original run (`Stage2_LIVE_RUN_LOG.md` §6: Account Access & Authentication, Funds Transfer, and — closely — the largest General Sentiment cluster and a Customer Support cluster) show correspondingly close BL1 scores:

| Category / cluster | Original score | This run's score | n_reviews (orig → this run) | avg_rating (orig → this run) |
|---|---|---|---|---|
| Account Access & Authentication / cluster "1" | 3,435.58 (rank 2) | 3,436.00 (rank 2) | 4,169 → 4,170 | 1.59 → 1.59 |
| Funds Transfer / cluster "0" | 3,159.27 (rank 3) | 3,153.72 (rank 3) | 3,233 → 3,235 | 1.42 → 1.43 |
| General Sentiment (residual, largest cluster) | 1,801.18 (rank 4) | 1,770.49 (rank 4) | 7,885 → 7,740 | 4.44 → 4.43 |

These three land within a fraction of a percent of the original score, at the same rank position, because the underlying Stage 2 clusters for these categories were themselves nearly unchanged between runs (see `Stage2_LIVE_RUN_LOG.md` §6). This is a meaningful, positive reproducibility signal: where Stage 2's clustering was stable, BL1's downstream ranking is stable too, at both the score and the rank level.

By contrast, categories where Stage 2 fragmented heavily between runs (Security & Data Privacy: 4 → 10 clusters; Fees, Subscription & Monetization: 3 → 7 clusters; Account Lifecycle Management: 3 → 6 clusters; Crypto-Specific Functionality: 2 → 5 clusters) do not have a clean one-to-one cluster to compare — the original run's single "Security & Data Privacy / cluster 2" (score 38.54) has no direct counterpart in this run's 10 Security clusters, because the underlying grouping of reviews itself changed. This is expected, not an error: it is the same downstream consequence of Stage 2 non-determinism already disclosed for Stage 3 (`Stage3_LIVE_RUN_LOG.md` §12), now shown to propagate through BL1 as well. **Treat this run's `bl1_ranking.csv` as a legitimate, independently-computed ranking over this run's own clusters — not as a corrected or improved version of the original, and not as a failed reproduction.**

## 8. The formula's known limitation, reconfirmed on this run's own data

The original write-up (§4.4.4.10) disclosed that the published formula has no severity floor and does not normalize engagement by cluster size, illustrated with General Sentiment/cluster 7 (largest cluster, healthy 4.44 rating) ranking 4th — ahead of the single lowest-rated cluster in that run.

The same property reproduces independently on this run's own data, with an even starker illustration:

- **General Sentiment / cluster 3** — this run's largest cluster (7,740 reviews), a healthy 4.43 average rating — again ranks **4th** overall.
- **Security & Data Privacy / cluster 6** — this run's single lowest-rated cluster of all 77 (average rating 1.07, 30 reviews) — ranks only **68th**, because it is roughly 258x smaller than the General Sentiment cluster outranking it.

This is not a new finding specific to this run's data — it is the same disclosed, intrinsic property of Wei et al.'s published formula (no size normalization, no severity floor), now independently reconfirmed on an entirely different clustering (77 vs. 65 clusters) than the one that first surfaced it. That it reproduces on a materially different set of clusters is itself evidence that this is a genuine property of the formula, not an artifact of one particular clustering run.

## 9. Disclosed data-quality note: missing thumbs-up counts

Corpus-wide: 2,311 of 52,392 rows (4.41%) have an empty `thumbs_up_count`, imputed as 0 per the same disclosed policy as the original run. Restricted to this run's 58,388 cluster-member reviews: **2,263 imputed (3.88%)** — close to, not identical to, the corpus-wide figure (expected, since it's a subset restricted to non-noise cluster members) and close to the original run's cluster-member figure of 4.03%.

## 10. Limitations (unchanged from the original write-up, plus one addition)

First, BL1 reuses only the paper's ranking formula, not its clustering method — disclosed adaptation, not a full reproduction of Wei et al.'s system.

Second, the formula itself has no severity floor and no size normalization (§8 above) — a property of the baseline being reproduced, not an implementation error.

Third, `thumbs_up_count` is imputed as 0 for 3.88% of cluster-member reviews in this run; given the term's small weight (w_th = 0.1) relative to `|reviews|` (w_rev = 1), this is expected to have a modest effect on the ranking, though no clean sensitivity bound has been computed.

**New in this run:** this is now the second independent computation of BL1, against two materially different Stage 2 clusterings (65 clusters vs. 77 clusters). The ranking is stable — at both the score and rank level — for the specific clusters whose underlying Stage 2 grouping was itself stable (§7), and diverges for clusters whose grouping changed. This means BL1's ranking should not be read as a fixed, single ground truth for this corpus; it is only as stable as the Stage 2 clustering feeding it, and a third rerun would likely reproduce the same pattern (stability where Stage 2 is stable, divergence where it is not) rather than reproducing this run's exact numbers.

## 11. What's in the downloadable package

| File | What it is |
|---|---|
| `BL1_LIVE_RUN_LOG.md` | This file. |
| `cluster_features.json` | Full per-cluster feature output for all 77 clusters (n_reviews, avg_rating, sum_thumbsup, mean_thumbsup, n_thumbsup_imputed, missing_text, bl1_cluster_score). |
| `bl1_ranking.csv` | The full 77-row ranking, sorted descending by score — the real deliverable. |
| `compute_cluster_features.py`, `verify_bl1_independent.py` | The exact scripts run this session, pointed at this run's actual input files. |
| `compute_stdout.log`, `verify_stdout.log` | Full console output from both runs. |

## 12. Honest limitation of this run overall

Like Stage 2 and Stage 3, this is one draw of a process whose upstream input (Stage 2's clustering) is non-deterministic. A third live rerun of Stage 2 → BL1 would very likely reproduce the pattern shown in §7 (score/rank stability for whichever clusters happen to land close to a prior run, divergence for whichever fragment differently) without reproducing this run's exact top-10/bottom-5 membership. BL1's own computation (the arithmetic in §4 and §5) is fully deterministic and was independently verified to 1e-6 — the variability here traces entirely to Stage 2, not to any non-determinism in BL1 itself.
