# stage4_prioritization/bl1_ClsuterScore/

**BL1**: the rule-based `ClusterScore` ranking formula from Wei, Courbis,
Lambolais, Xu, Bernard & Dray (2023, arXiv:2311.03058) —
`ClusterScore = (w_rev·|reviews| + w_th·|thumbsup|) / (w_ra·rating)`, published
default weights (1, 0.1, 1) used unmodified. Only the ranking formula is reused,
not the original paper's own clustering method — it ranks this project's own Stage
2 clusters. Pure arithmetic, no LLM or human judgment involved.

(Folder name is spelled "ClsuterScore" — a typo in the original folder name,
preserved verbatim rather than silently corrected, since renaming it could break
any path reference elsewhere.)

| File | What it is |
|---|---|
| `BL1_LIVE_RUN_LOG.md` | The full run log — read this first. |
| `cluster_features.json` | Per-cluster features for all 77 clusters (n_reviews, avg_rating, sum_thumbsup, mean_thumbsup, n_thumbsup_imputed, missing_text, bl1_cluster_score). |
| `bl1_ranking.csv` | **The real deliverable** — all 77 clusters ranked descending by score. |
| `compute_cluster_features.py` | Computes the features and score from Stage 2's cluster assignments + the corpus. |
| `verify_bl1_independent.py` | Independently re-derives `bl1_cluster_score` from the raw corpus/assignment files (not from `compute_cluster_features.py`'s own stored, rounded output) — 77/77 clusters matched to within 1e-6, 0 mismatches. |
| `compute_stdout.log`, `verify_stdout.log` | Full console output from both scripts. |

## Result summary (this run, 77 clusters)

Top-ranked: Customer Support Quality (score 3,468), Account Access & Authentication
(3,436), Funds Transfer (3,154). Bottom-ranked: Charting, Analytics & Professional
Tools (score 7.38). Mean 405.7, median 102.2 — heavily right-skewed, as expected
from a formula whose numerator scales with raw review count.

**Known limitation of the formula itself** (not this implementation): no severity
floor and no size normalization. This run's largest cluster (General Sentiment,
7,740 reviews, 4.43★ average) ranks 4th overall, ahead of the single lowest-rated
cluster of all 77 (1.07★, only 30 reviews, ranks 68th) — purely because it is
~258x larger.
