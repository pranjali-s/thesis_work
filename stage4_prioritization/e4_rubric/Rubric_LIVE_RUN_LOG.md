# Stage 4 Rubric — Live Run Log

**Run date:** 2026-09-24
**Scope:** Full re-derivation of the 6-dimension LLM-applied prioritization rubric against this session's live 77-cluster Stage 2/3 output, to the same standard of rigor and disclosure as the original 65-cluster run (`Stage4_rubric_writeup.md`).

## 1. What the rubric is

Six dimensions — reach, severity, engagement, recency, cross-platform generality, actionability — each scored 1–10 per Stage 3 roadmap item, informing a holistic `overall_priority` (1–10) plus a short justification. As in the original run, `overall_priority` is disclosed as a holistic judgment informed by the six dimension scores and the underlying cluster data, not a fixed formula mechanically combining them.

## 2. Disclosed methodological adaptation this run

The original run scored all six dimensions purely as LLM holistic judgment. This run makes an explicit, disclosed adaptation for reproducibility and auditability: the four dimensions with an unambiguous numeric basis in this project's own already-computed data — **reach**, **severity**, **engagement**, **recency** — plus **cross-platform generality** (count of distinct apps present in a cluster) were computed via disclosed, deterministic formulas rather than re-derived by holistic reading each time:

- **Reach** = decile rank of `n_reviews` among the 77 clusters (1 = smallest, 10 = largest).
- **Severity** = linear inverse mapping of `avg_rating`: `round(1 + (5 − avg_rating) / 4 × 9)`, clamped to [1, 10] (a 1★ average maps to 10, a 5★ average maps to 1).
- **Engagement** = decile rank of `mean_thumbsup` among the 77 clusters.
- **Recency** = `frac_recent_third` (the fraction of a cluster's reviews falling in the most recent third of the corpus's date range, freshly computed this run from `Stage2_live`'s review dates) mapped linearly to [1, 10].
- **Cross-platform generality** = count of distinct apps present in the cluster, mapped `{1 app→2, 2 apps→6, 3 apps→10}`.

**Actionability** and the holistic **`overall_priority`** (plus justification) were genuinely, individually judged for all 77 clusters by reading each cluster's real title, description, and sample quotes — not computed from a formula — preserving the original run's core methodological claim that overall priority is a holistic judgment, not a mechanical combination.

This adaptation is disclosed because it is real: it trades some of the original's "everything is LLM judgment" purity for reproducibility on the five dimensions that have an unambiguous quantitative basis, while preserving genuine holistic judgment exactly where it matters most — deciding whether a cluster's complaint is specific and fixable (actionability), and weighing severity against reach and fixability together (overall_priority).

## 3. Inputs

| Input | Source |
|---|---|
| 77 Stage 3 roadmap items (title, description, quotes) | `/home/claude/Stage3_live/stage3_roadmap_items.json` |
| n_reviews, avg_rating, mean_thumbsup | `/home/claude/BL1_live/cluster_features.json` |
| delta_rating_app, apps_present | `/home/claude/E1_live/cluster_features_bl2.json` |
| frac_recent_third, median_review_date | freshly computed this run from `Stage2_live/clusters/cluster_assignments.csv` + `Stage2_live/batches/batch_001.csv` review dates |

Corpus review-date range confirmed directly: 2024-08-15 to 2026-08-15 (52,392 reviews). Recent-third cutoff computed by date-range thirds (not review-count thirds): 2025-12-15.

## 4. Execution

**Step 1 — merge quantitative inputs and compute 5 dimensions** (`stage4_input_items_live.json` build, inline): reach/engagement via decile rank, severity via linear rating inversion, recency via `frac_recent_third`, cross-platform via distinct-app count. All 77 clusters received a value for all 5 dimensions — 0 missing.

**Step 2 — actionability + overall_priority + justification** (`rubric_judgment_scores.py`): each of the 77 clusters' title/description/quotes was read individually and scored. Console-confirmed: `missing judgment keys: []`, `total judged: 77`.

**Step 3 — merge** (`build_stage4_rubric.py`): combined into `stage4_scores_merged_live.json`, 77 rows.

**Step 4 — independent verification** (`verify_stage4_rubric_merge_live.py`), which does not trust the merged file and re-derives everything from the two source inputs:

```
1. Key set equality: PASSED (77 keys match exactly)
2. No duplicates: PASSED (77 rows, 77 unique keys)
3. Field-value fidelity vs. JUDGMENT source: 0 mismatches / 77 rows
4. Scale check: 0 out-of-scale values / 539 values checked (77 clusters x 7 dimensions)

ALL CHECKS PASSED.
```

## 5. Results

**Distribution (n = 77, `overall_priority`, 1–10 scale):** minimum 1, maximum 10, mean 4.53, median 4. Distribution: 1→30, 2→1, 3→4, 4→4, 5→2, 6→8, 7→10, 8→7, 9→5, 10→6. Compared to the original 65-cluster run (mean 4.77, median 4, fairly even spread), this run's distribution is more bottom-heavy — 30 of 77 clusters (39%) score at the floor, reflecting this run's larger share of pure-praise clusters (General Sentiment, Usability & Navigation, and several Crypto-Specific / Onboarding clusters all resolved to generic positive sentiment with no actionable content).

**Top 6 clusters (`overall_priority` = 10):**

| Category / cluster | Title |
|---|---|
| ACCOUNT_ACCESS_AUTH/1 | Login lockouts from a mix of causes, most often generic identity verification failures |
| APP_STABILITY_PERFORMANCE/2 | Slowness, freezing, and crashes during active trading |
| APP_STABILITY_PERFORMANCE/3 | App fails to open, crashes, or breaks after updates |
| CUSTOMER_SUPPORT/1 | Support seen as slow, bot-gated, and unhelpful across platforms |
| FUNDS_TRANSFER/0 | Withdrawals blocked by holds, freezes, and verification loops |
| TRADE_EXECUTION/1 | Blocked trades, price slippage, and unreliable stop-loss execution |

As in the original run, the top of the ranking is dominated by severe, specific, actionable failures rather than simply the largest clusters — the rubric doing what it is designed to do, separating severity and actionability from raw reach.

**30 clusters tied at the floor (`overall_priority` = 1)** are, without exception, pure positive-sentiment clusters (praise for stability, low fees, ease of use, onboarding, general sentiment) with no actionable complaint — consistent with how BL1 and E2 both independently treat these same kinds of clusters.

## 6. Limitations

Same core limitation as the original run: `overall_priority` and `actionability` are holistic judgment (this session's own reading of each cluster), with no independent human check performed. This carries the same circularity caveat already disclosed throughout this project for LLM-judgment steps (Stage 1's classifier, Stage 3's quality ratings, E2's match review).

**New, disclosed this run:** five of the seven scored dimensions were computed via deterministic formulas rather than independently re-judged by reading each cluster (Section 2) — a real adaptation from the original's "every dimension is LLM judgment" approach, made explicitly for reproducibility. This means this run's rubric is not a pure replication of the original methodology; it is a disclosed hybrid (deterministic dimensions + genuine holistic judgment on actionability/overall_priority) that should be read as such when compared to the original 65-cluster results.

## 7. Files

`stage4_input_items_live.json` (merged quantitative inputs + 5 computed dimensions), `rubric_judgment_scores.py` (actionability/overall_priority/justification judgment source), `build_stage4_rubric.py` (merge script), `stage4_scores_merged_live.json` (final 77-row scored output), `verify_stage4_rubric_merge_live.py` (independent verification), `verify_stage4_rubric_merge_live_stdout.log`.
