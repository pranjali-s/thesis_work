# stage4_prioritization/

Stage 4 (§4.4.4 / RQ4b): three competing methods for ranking Stage 3's 77
roadmap items by priority, plus the evaluation pipeline that checks whether any of
them tracks what the three companies actually shipped. All four subfolders are the
live rerun (2026-09-24), chained off this same tree's `stage2_clustering/` and
`stage3_summarization/` output.

| Subfolder | What it is | RQ role |
|---|---|---|
| `bl1_ClsuterScore/` | **BL1** — rule-based `ClusterScore` formula from Wei et al. (2023), reused unmodified. Pure arithmetic, no LLM/human judgment. | Baseline 1 |
| `bl2_random_forest/` | **BL2** — trained Random Forest baseline adapted from Scalabrino et al. (2017). Also contains this run's live E1 (release-note) re-collection and E2 (cluster-to-release matching), since BL2 needs E2's labels to train against. | Baseline 2, + E1/E2 |
| `e1_release_note_scraper/` | A **separate, more elaborate** research-grade release-note/version-history scraper. Its output does **not** appear to be what actually fed BL2/E4 this run — see below. | Related tooling, not the E1 source actually used |
| `e4_rubric/` | The **LLM-applied 6-dimension prioritization rubric**, and **E4**, the rank-agreement evaluation comparing rubric/BL1/BL2 against E2's ground truth and against each other. | RQ4b's headline evaluation |

## Which E1 data actually fed BL2 and E4 — read this before citing E1 numbers

There are two independent E1 (release-note) collection efforts on this machine,
and only one of them is what this run's BL2/E4 results are actually built on:

- **`bl2_random_forest/build_e1.py`** — a focused scraper (iTunes Lookup API +
  Apple RSS reviews-style endpoints are not used here; it hits Trading 212's
  Discourse JSON API, Robinhood's newsroom/sitemap, and Coinbase's blog listing
  pages directly) that produced **147 real, dated release notes** on 2026-09-24
  (`e1_release_notes.csv`, 94 Trading 212 / 16 Robinhood / 37 Coinbase). **This is
  the file `candidate_matching.py`, `review_e2_matches.py`, and everything in
  `e4_rubric/` actually consumes.**
- **`e1_release_note_scraper/collect_company_updates.py`** — a separately-written,
  broader research tool (same three companies, same idea, different and more
  elaborate implementation — also produces Apple version-history parsing,
  feature-candidate sentence extraction, help-article change tracking). Its own
  README discloses that live company-page crawling "remains unverified in this
  execution environment" (the sandbox it was packaged in returned an unavailable
  placeholder for the live company pages), and its shipped example output
  (`verified_examples_no_start_limit_2026-09-24.csv`) is only **23 manually-checked
  examples** — a different size and shape from the 147-row dataset BL2/E4 actually
  used.

Both scripts are real and neither fabricates data. But if you're tracing a specific
E1 number in the thesis text back to its source script, it almost certainly traces
to `bl2_random_forest/build_e1.py`, not `e1_release_note_scraper/`. If you intended
the more elaborate scraper to be the actual E1 source going forward, that is a
choice worth making explicit in the write-up, since right now the two tools coexist
without either one's README saying which one is authoritative.

## The headline finding of this run (all disclosed in `e4_rubric/E4_LIVE_RUN_LOG.md`)

This run's E2 found **0 real matches out of 77 clusters** (vs. the original run's
2/65) — a more severe version of the same finding. With zero positives: BL2 cannot
be trained meaningfully (its Random Forest degenerates to always predicting
"negative"), and every ground-truth-based metric in E4 (Precision@k, MRR, Spearman
vs. E2) is mathematically undefined for all three methods, not just weak. The one
comparison that remains meaningful this run is rubric-vs-BL1 pairwise agreement
(Spearman rho = 0.408, p < 0.001) — weaker than the original run's 0.675, but still
real and significant. None of this is an error in this run's code; it is the
disclosed, expected consequence of how few real, content-verified cluster-to-
release matches exist in this project's actual data, confirmed for a second time
on an independently-collected E1 dataset.
