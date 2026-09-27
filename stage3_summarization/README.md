# stage3_summarization/

Stage 3 (§4.4.3): turns each of Stage 2's 77 non-noise clusters into a structured
"roadmap item" (title, description, 2-3 verbatim quotes), following the project's
8-step methodology (prep → generate → merge+completeness → independent grounding
verification → blind adversarial rating → investigate+correct flagged issues →
build-not-run the human-rating upgrade path → write the run log). This is the live
rerun, chained directly off this same folder tree's `stage2_clustering/` output —
see `STAGE3_RUN_LOG.md` for the full account.

| File / folder | What it is |
|---|---|
| `STAGE3_RUN_LOG.md` | The full run log — read this first. |
| `prep/` | 77 per-cluster input files (the sampled review text each generation agent actually saw). See its own README. |
| `prep_manifest.json` | The authoritative 77-entry manifest for the files in `prep/`. |
| `outputs/` | Raw, pre-merge generation output from the 6 parallel LLM subagents. See its own README. |
| `ratings/` | Raw, pre-merge blind adversarial rating output from a second, independent set of 6 subagents. See its own README. |
| `stage3_roadmap_items.json` / `.csv` | **The real output of this stage** — 77 items, post-correction. 9 of the 77 items carry `"corrected": true` plus a `correction_note` (see below). |
| `stage3_roadmap_items.json.bak_pre_fix` | The pre-correction version, kept so the original (flawed) generation output stays inspectable rather than silently overwritten. |
| `stage3_ratings.json` / `stage3_ratings_summary.json` | The 77 AI blind-rating results (merged) and aggregate/per-category stats. Aggregate: faithfulness 4.49/5, clarity 4.55/5, usefulness 3.40/5. |
| `grounding_check_report.json` | Independent grounding check result: 231/231 quotes verified as real, correctly-attributed, exact substrings. **Genuinely complete despite its small (101-byte) size** — it's a compact pass/fail summary with empty error arrays, not a truncated file. |
| `verify_grounding.py`, `merge_outputs.py`, `merge_ratings.py`, `prep_clusters.py` | The exact scripts run this session. |
| `investigate_flags.py` | The independent, from-scratch re-investigation script for the 9 faithfulness issues below — rerunnable, shows its work. |
| `human_rate_stage3.py` | A terminal tool for real human rating of all 77 items. **Built and smoke-tested only — no human has rated any item through it.** Every rating in this package is the AI-only blind pass. |

## The 9 corrected items — read before citing any Stage 3 statistic verbatim

The blind rating pass flagged 9 items with genuine faithfulness problems (an
ungrounded detail, an overstated proportion, a miscounted statistic, etc.). Per the
project's standing rule, **none were corrected on a subagent's word alone** — each
was independently re-investigated by directly reading the real sampled review text
in `prep/` and, where a proportion was in question, recomputing it from scratch
(`investigate_flags.py`). All 9 were confirmed genuine and corrected; the full
before/after table with each item's independent verification is in
`STAGE3_RUN_LOG.md` §8.

## Honest limitation carried forward

This run is one draw of a process with two independent layers of variance stacked
on each other: Stage 2's non-deterministic clustering (77 vs. 65 clusters going in)
and Stage 3's own LLM generation/rating variance. Re-running Stage 3 again — even
against this exact same `cluster_assignments.csv` — would very likely surface a
different set of faithfulness issues than the 9 found here, not necessarily a
larger or smaller one.
