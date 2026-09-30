# stage4_prioritization/e4_rubric/

Two things live in this folder: **the LLM-applied prioritization rubric** (6
scored dimensions + a holistic overall priority) and **E4**, the rank-agreement
evaluation that checks whether the rubric, BL1, or BL2 track what the three
companies actually shipped. Both are the live rerun (2026-09-24), against this
tree's 77-cluster Stage 2/3 output.

| File | What it is |
|---|---|
| `Rubric_LIVE_RUN_LOG.md` | Full run log for the rubric — read this first if you want the rubric's own methodology and results. |
| `E4_LIVE_RUN_LOG.md` | Full run log for E4 — read this first if you want the cross-method evaluation. |
| `stage4_input_items_live.json` | The 77 clusters merged with 5 deterministically-computed dimensions (reach, severity, engagement, recency, cross-platform generality — see below). |
| `rubric_judgment_scores.py` | Where **actionability** and **overall_priority** (+ justification) were genuinely, individually judged per cluster by reading its real title/description/quotes — not computed from a formula. |
| `build_stage4_rubric.py` → `stage4_scores_merged_live.json` | The final, merged 77-row rubric output. |
| `verify_stage4_rubric_merge_live.py` | Independently re-derives the merge from the two source inputs — all 4 checks (key equality, no duplicates, field fidelity, scale bounds) passed. |
| `compute_e4_live.py` → `e4_results_live.json`, `e4_rankings_full_live.csv` | Precision@k / MRR / Spearman of each method vs. E2 ground truth, plus pairwise Spearman between the three methods. |
| `verify_e4_independent_live.py` | Independently re-reads the three raw source files and re-derives E4's numbers directly — 0 mismatches. |

## Disclosed methodological adaptation (rubric)

This run computes 5 of the 6 rubric dimensions deterministically — **reach**
(decile rank of n_reviews), **severity** (linear inverse mapping of avg_rating),
**engagement** (decile rank of mean_thumbsup), **recency** (fraction of reviews
in the corpus's most recent third), and **cross-platform generality** (count of
distinct apps) — while **actionability** and **overall_priority** remain genuine,
individually-read holistic judgment for all 77 clusters. This is a disclosed
hybrid rather than "every dimension is LLM judgment," trading some judgment
purity for reproducibility while preserving genuine judgment exactly where it
matters most (deciding whether a complaint is specific/fixable, and weighing
severity against reach together).

## The central E4 finding — read before citing any metric here

This run's E2 (in `../bl2_random_forest/`) found **0 real matches out of 77
clusters**. With zero positives, Precision@k, MRR, and Spearman-vs-ground-truth are
not merely underpowered — they are **mathematically undefined** for all three
methods, reported as `null` with an explanatory note rather than a misleading
`0.0`. **BL2 is further excluded from the pairwise comparisons too**: trained on an
all-negative target, its output has zero variance, so any correlation against it is
also undefined. The one comparison this run's data still supports is **rubric vs.
BL1**: Spearman rho = 0.408 (p = 0.0002) — a real, statistically significant
relationship. Read `E4_LIVE_RUN_LOG.md` §2 and §6 before using any number from
this folder in the thesis text.
