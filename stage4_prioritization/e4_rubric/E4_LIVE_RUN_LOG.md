# E4 (Rank-Agreement Evaluation) — Live Run Log

**Run date:** 2026-09-24
**Scope:** Evaluates the rubric, BL1, and BL2 rankings of this session's live 77-cluster output against E2's real-release-match ground truth, and against each other — to the same standard as the original run (`Stage4_E4_writeup.md`).

## 1. What E4 is

E4 checks whether the rubric's, BL1's, and BL2's priority rankings track what the three companies actually shipped, using E2's `e2_matched` label as ground truth: Precision@k, MRR, and Spearman correlation of each method's score against the real-match label, plus pairwise Spearman correlation between the three methods' own rankings (a secondary diagnostic of whether the methods agree with each other, independent of ground truth).

## 2. The central, unavoidable finding — stated before any number

**This run's E2 found 0 real matches out of 77 clusters (0.0%)** — see `E2_FULL_TECHNICAL_WRITEUP.md`. The original run's E4 already carried a severe caveat with 2/65 positives (too few for any metric to be statistically powered). This run is a step further: with **zero** positive examples, Precision@k, MRR, and Spearman correlation against the ground truth are not merely underpowered — they are **mathematically undefined** for every method, not a computable-but-weak number. There is nothing for Precision@k or MRR to find, and Spearman correlation against a constant (all-zero) label has no variance to correlate against. This script computes and reports this explicitly (`None` with an explanatory note), rather than reporting a misleading `0.0`.

**BL2 is further excluded from all ranking-based analysis in this run specifically.** BL2's Random Forest was trained on an all-negative target (Section on BL2), so its `predict_proba` output has a single class and zero variance — every cluster receives an identical, uninformative score. A Spearman correlation against a zero-variance ranking is undefined for the same mathematical reason as the ground-truth case above. This means this run's E4 can only meaningfully evaluate the **rubric vs. BL1** pairwise relationship — a real, disclosed narrowing from the original run's three-way comparison.

## 3. Inputs

| Input | Source |
|---|---|
| Rubric `overall_priority` (77 clusters) | `stage4_scores_merged_live.json` (this session, Section on Rubric) |
| BL1 `bl1_cluster_score` (77 clusters) | `/home/claude/BL1_live/bl1_ranking.csv` |
| E2 `e2_matched` ground truth (77 clusters) | `/home/claude/E1_live/e2_final.json` |
| BL2 status (for exclusion rationale) | `/home/claude/E1_live/bl2_metadata.json` |

## 4. Execution

**Script:** `compute_e4_live.py`. Console output:

```
Joined 77 clusters on (category, cluster_id) -- exact key match confirmed across rubric, BL1, and E2 sources.
E2 ground truth: 0 positive / 77 negative out of 77.

Rubric vs. BL1 Spearman rho = 0.4078 (p=0.0002318)
Rubric vs. BL2 and BL1 vs. BL2: undefined (BL2 output has zero variance this run).
All ground-truth-based metrics (Precision@k, MRR, Spearman vs. E2) are undefined for all three methods this run: E2 has 0 positive examples.

Wrote e4_results_live.json and e4_rankings_full_live.csv
```

**Independent verification** (`verify_e4_independent_live.py`, re-reads the three raw source files directly rather than trusting `compute_e4_live.py`'s own stored output):

```
Recomputed independently: n_clusters=77, n_positive_e2=0, rubric_vs_bl1 rho=0.4078 (p=0.0002318)

All values matched exactly -- 0 mismatches. PASSED.
```

## 5. Results

**Ground-truth-based metrics (Precision@k, MRR, Spearman rho vs. E2):** undefined for all three methods (rubric, BL1, BL2) — 0 positive examples in this run's E2 ground truth. Reported as `null` with an explanatory note in `e4_results_live.json`, not as a misleading `0.0`.

**Pairwise Spearman correlation between methods' own rankings:**

| Pair | rho | p |
|---|---|---|
| Rubric vs. BL1 | 0.4078 | 0.0002 |
| Rubric vs. BL2 | undefined | — |
| BL1 vs. BL2 | undefined | — |

## 6. Reading these numbers honestly

**Rubric vs. BL1 agree moderately and significantly (rho = 0.41, p < 0.001)** — weaker than the original run's 0.675, but still a real, statistically significant positive relationship between two differently-built methods (one holistic multi-dimension judgment, one a fixed published formula). This is consistent with the original run's finding that both methods pick up on a real, shared "this looks important" signal even when built completely differently.

**BL2 cannot be compared to anything this run.** Not because it disagrees with the rubric or BL1 — there is no signal in its output at all to agree or disagree with. This is a direct, mechanical consequence of BL2's own headline finding (Section on BL2): trained on 0 positive examples, it can only ever predict "negative," uniformly, for every cluster.

**No claim can be made about how well any method predicts real company action this run.** Unlike the original run, which could at least report where the 2 real matches landed in each ranking (rubric/BL1 in the upper-middle, BL2 near the bottom — actively worse than chance), this run has no real matches to locate in any ranking at all. The honest, complete finding is: **this run's E4 cannot evaluate predictive validity against ground truth for any method** — not a weak result, an absent one, and this is inherited entirely from E2's 0/77 finding, not from any flaw in how E4 itself was built.

## 7. Comparison to the original run

| | Original run (65 clusters) | Live rerun (77 clusters) |
|---|---|---|
| E2 positives | 2/65 | 0/77 |
| Precision@k / MRR / Spearman vs. ground truth | Computable but severely underpowered (all p > 0.25) | Mathematically undefined for all 3 methods |
| Rubric vs. BL1 pairwise rho | 0.675 (p<0.001) | 0.408 (p<0.001) — still significant, weaker |
| BL1 vs. BL2 pairwise rho | 0.436 (p<0.001) | undefined — BL2 has zero-variance output this run |
| Rubric vs. BL2 pairwise rho | 0.340 (p=0.006) | undefined — BL2 has zero-variance output this run |
| Overall conclusion | No method demonstrates validated predictive ability; BL2 performs worse than chance | Same overall conclusion, more severe: ground-truth-based evaluation is not just weak but impossible this run for any method, and BL2 cannot be evaluated against the other two methods at all |

Both runs converge on the same underlying finding, restated more starkly this time: this project's E1/E2 evaluation data is too sparse to validate any prioritization method against, on this project's real (not synthetic) data. The rubric and BL1 continue to show a real, significant relationship with each other independent of ground truth, which is the one comparison this run's data still supports.

## 8. Limitations

- The central limitation (Section 2) is not repeated in full here: 0 positive ground-truth examples means no metric requiring ground truth is computable this run, for any method.
- BL2's exclusion from all ranking comparisons is a direct, disclosed consequence of its own degenerate training outcome (Section on BL2), not a separate new finding.
- The rubric's own adaptation this run (5 of 7 dimensions computed deterministically rather than by holistic re-reading, Section on Rubric) means this run's rubric-vs-BL1 comparison is not a pure like-for-like replication of the original run's comparison — both the rubric's construction and E4's underlying ground truth differ from the original run.
- As in the original run, any result here describes this project's specific data (three trading apps, PR-oriented release notes, one snapshot in time) and should not be read as a general verdict on Wei et al. (2023)'s or Scalabrino et al. (2017)'s methods, or on LLM-based rubrics generally.

## 9. Files

`compute_e4_live.py`, `compute_e4_live_stdout.log`, `e4_results_live.json`, `e4_rankings_full_live.csv`, `verify_e4_independent_live.py`, `verify_e4_independent_live_stdout.log`.
