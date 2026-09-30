# Stage 3 — LLM-Assisted Structured Summarization (`stage3_summarization/`)

**Full documentation, verified file inventory, and reproduction guide.**
Everything under "Independently verified this session" was checked directly
against the actual files in this folder (row counts, sampling totals, the 9
corrected items, quote counts, rating distributions — all recomputed from
`prep_manifest.json`, `stage3_roadmap_items.json`, `stage3_ratings.json`, and
`grounding_check_report.json` themselves) — not copied from the folder's own
README/log claims. Where something could not be verified from these files
alone, that's stated explicitly.

---

## 1. What this folder is

This is **Stage 3 of the pipeline (thesis §4.4.3)**: it turns each of Stage
2's 77 non-noise clusters into a structured "roadmap item" — a title, a
1–3 sentence description, and 2–3 verbatim supporting quotes linked to real
review IDs. Unlike Stage 1 (a scripted batch API call) or Stage 2 (pure ML,
no LLM at all), this stage is genuinely LLM-assisted throughout: generation
and quality rating are both done by dispatching Claude Sonnet 5 as parallel
subagents (via the Agent/subagent-dispatch tool), not by a single scripted
API call.

This run was executed 2026-09-24, chained directly off this same folder
tree's `stage2_clustering/` output (`cluster_assignments.csv`, 77 non-noise
clusters, 58,388 non-noise review-cluster observations). It followed an
8-step methodology: prep → generate (6 parallel subagents) → merge +
completeness check → independent grounding verification → blind adversarial
rating (6 fresh subagents) → investigate and correct flagged issues → build
(not run) a human-rating upgrade path → write the run log.

---

## 2. Verified file inventory

| File / folder | What it is | Verified this session |
|---|---|---|
| `STAGE3_RUN_LOG.md` | The full run log — environment, step-by-step console output, the 9-item correction table, timeline | ✅ Present, read in full |
| `README.md` | Folder overview and file table | ✅ Present, read in full |
| `prep_clusters.py` | Step 1 — joins cluster assignments to review text, samples/chunks | ✅ Present, read in full; hardcoded-path notice added this session (§5) |
| `merge_outputs.py` | Step 3 — merges the 6 generation-group files, completeness check | ✅ Present, read in full |
| `verify_grounding.py` | Step 4 — independent grounding check | ✅ Present, read in full; hardcoded-path notice added this session (§5) |
| `merge_ratings.py` | Step 5 merge — merges the 6 rating-group files, aggregate stats | ✅ Present, read in full |
| `investigate_flags.py` | Step 6 — independent, from-scratch re-investigation of the 9 flagged items | ✅ Present, read in full; rerunnable, shows its own regex/keyword searches |
| `human_rate_stage3.py` | Step 7 — terminal human-rating tool | ✅ Present, read in full. **Built and smoke-tested only — no human has rated any item through it.** |
| `prep_manifest.json` | Authoritative 77-entry manifest (n_total/n_sampled/n_chunks per cluster) | ✅ Present; **independently recomputed from this file: 77 entries, sums to 58,388 n_total / 9,912 n_sampled, 0 missing text, 49 clusters requiring sampling, 71 requiring chunking — all match `STAGE3_RUN_LOG.md`'s reported console output exactly** |
| `prep/` | 77 per-cluster input files (`<CATEGORY>__<cluster_id>.json`), the actual sampled review text each subagent read | ✅ Present; **77 files confirmed, category-prefix counts cross-checked against `prep_manifest.json` and against Stage 2's own 77-cluster breakdown — exact match on all 17 categories** |
| `outputs/group1.json`–`group6.json` | Raw, pre-merge generation output, one file per subagent dispatch | ✅ Present; item counts (11+12+17+13+12+12 = 77) match `STAGE3_RUN_LOG.md` |
| `ratings/group1_ratings.json`–`group6_ratings.json` | Raw, pre-merge rating output | ✅ Present |
| `stage3_roadmap_items.json` / `.csv` | **The real output of this stage** — 77 structured items, post-correction | ✅ Present; **independently recomputed: 77 items, 77 unique (category, cluster_id) keys with zero duplicates/missing/extra against `prep_manifest.json`, 231 total quotes, 9 items with `corrected: true`** |
| `stage3_roadmap_items.json.bak_pre_fix` | Pre-correction version, kept for audit | ✅ Present |
| `stage3_ratings.json` / `stage3_ratings_summary.json` | Merged AI blind-rating results and aggregate/per-category stats | ✅ Present; **independently recomputed from the raw 77-row `stage3_ratings.json`: faithfulness 4.4935→4.49, clarity 4.5455→4.55, usefulness 3.4026→3.40 — exact match to `stage3_ratings_summary.json`'s reported aggregate. Rating distributions recomputed and confirmed exactly: faithfulness [0,2,6,21,48], clarity [0,0,4,27,46], usefulness [5,12,23,21,16] (1→5 score buckets). 18 items flagged ≤2 on some dimension, confirmed by independent recount** |
| `grounding_check_report.json` | Independent grounding check result | ✅ Present; **231/231 quotes verified (0 unknown IDs, 0 wrong-cluster, 0 ungrounded) — matches the JSON file's own `passed: true` and the counts recomputed from `stage3_roadmap_items.json`'s 231 total quotes** |

**All files the run log claims should exist are present. No gaps found in
the file inventory** (unlike nothing — this is a complete, self-contained
package: every script, every raw per-subagent output, every intermediate
and final artifact is here).

---

## 3. Verified results (recomputed from the raw data files)

### 3.1 Sampling and chunking (from `prep_manifest.json`, 77 entries)

| Metric | Value |
|---|---:|
| Non-noise clusters covered | 77 |
| Total n_total (review-cluster observations across all 77 clusters) | 58,388 |
| Total n_sampled (reviews actually supplied to the LLM) | 9,912 |
| Sampling ratio | 16.98% (≈17.0%) |
| Reviews missing text | 0 |
| Clusters requiring sampling (n_total > 150) | 49 |
| Clusters requiring chunking (n_chunks > 1) | 71 |
| Smallest cluster | 24 reviews (`CHARTING_TOOLS` / cluster 0) |
| Largest cluster | 7,740 reviews (`GENERAL_SENTIMENT` / cluster 3) |

Per-category n_total (clustered observations) — cross-checked against Stage
2's own category totals:

| Category | n_total | n_sampled |
|---|---:|---:|
| ACCOUNT_ACCESS_AUTH | 4,289 | 269 |
| ACCOUNT_LIFECYCLE | 1,109 | 810 |
| ADVERTISING_NOTIFICATIONS | 520 | 407 |
| APP_STABILITY_PERFORMANCE | 4,272 | 532 |
| ASSET_COVERAGE | 1,007 | 463 |
| CHARTING_TOOLS | 1,013 | 174 |
| CRYPTO_SPECIFIC | 2,415 | 731 |
| CUSTOMER_SUPPORT | 4,452 | 245 |
| FEES_SUBSCRIPTION | 2,307 | 927 |
| FUNDS_TRANSFER | 4,136 | 403 |
| GENERAL_SENTIMENT | 12,545 | 1,050 |
| ONBOARDING_BEGINNER | 4,258 | 740 |
| PREDICTION_MARKETS | 248 | 248 |
| SECURITY_PRIVACY | 1,233 | 898 |
| TRADE_EXECUTION | 1,874 | 300 |
| TRUST_FAIRNESS_REGULATORY | 2,054 | 515 |
| USABILITY_NAV | 10,656 | 1,200 |
| **Total** | **58,388** | **9,912** |

### 3.2 Generation and completeness (from `STAGE3_RUN_LOG.md` §4–5 and recomputed from `stage3_roadmap_items.json`)

77 items produced across 6 parallel subagent dispatches (11+12+17+13+12+12 =
77). Merge completeness check: 0 duplicates, 0 missing, 0 extra — confirmed
independently by comparing the 77 (category, cluster_id) keys in
`stage3_roadmap_items.json` against `prep_manifest.json`'s 77 keys: exact
set match.

### 3.3 Grounding verification (from `grounding_check_report.json`)

231 total quotes checked. 0 unknown review IDs, 0 wrong-cluster attributions,
0 ungrounded (non-substring) quotes. `passed: true`.

### 3.4 Quality rating (recomputed from `stage3_ratings.json`, 77 rows)

| Dimension | Mean (recomputed) | Distribution (1/2/3/4/5) |
|---|---:|---|
| Faithfulness | 4.49 | 0 / 2 / 6 / 21 / 48 |
| Clarity | 4.55 | 0 / 0 / 4 / 27 / 46 |
| Usefulness | 3.40 | 5 / 12 / 23 / 21 / 16 |

18 of 77 items flagged ≤2 on at least one dimension (independently
recounted from the raw ratings — matches `stage3_ratings_summary.json`).

### 3.5 The 9 corrected items (recomputed: `corrected: true` count in `stage3_roadmap_items.json`)

| # | Category / cluster | Independent check this run confirmed |
|---|---|---|
| 1 | ACCOUNT_ACCESS_AUTH / 1 | Phone/2FA-change language in 10/150 (6.7%); generic verification-failure language in 40/150 (26.7%) |
| 2 | ASSET_COVERAGE / 1 | 4/150 sampled reviews show genuine first-time/new-user framing |
| 3 | CRYPTO_SPECIFIC / 1 | Of 89 positive-sentiment reviews, 12 (13.5%) use explicit beginner-framing language |
| 4 | FEES_SUBSCRIPTION / 3 | "Gold" mentioned in 44/91 (48.4%); transfer-fee language in 10/91 (11.0%) |
| 5 | ONBOARDING_BEGINNER / 4 | Keyword recount: 61/150 (not the originally stated 72/150) |
| 6 | SECURITY_PRIVACY / 7 | Only 2/34 (5.9%) use explicit phone/email-change language |
| 7 | SECURITY_PRIVACY / 9 | Only 2/28 (7.1%) cite a specific dollar figure |
| 8 | USABILITY_NAV / 5 | 0/150 describe a withdrawal delay; one review states the opposite |
| 9 | USABILITY_NAV / 6 | 0/150 sampled reviews mention the originally-cited detail at all |

Every one of these 9 numbers was independently recomputed this session
directly from the `prep/` files (not copied from `STAGE3_RUN_LOG.md`'s own
table) and matches exactly.

---

## 4. Environment needed for reproduction

| Requirement | Detail |
|---|---|
| Python | 3.11 (this run used 3.11.15) |
| Third-party packages | **None.** Every script (`prep_clusters.py`, `merge_outputs.py`, `verify_grounding.py`, `merge_ratings.py`, `investigate_flags.py`, `human_rate_stage3.py`) uses only the standard library (`csv`, `json`, `os`, `re`, `random`, `glob`, `collections`) |
| LLM access | Claude Sonnet 5 (model ID `claude-sonnet-5`), invoked via an Agent/subagent-dispatch tool capable of running multiple independent subagent instances in parallel — **not** a direct API script like Stage 1. Reproducing this stage requires an environment with that kind of subagent-dispatch capability, not just API credentials. |
| Input | Stage 1's full review corpus (batch CSVs with `review_id_hash`, `review_text`, `app`) and Stage 2's `cluster_assignments.csv` |

No `requirements.txt` is needed for this stage — there is nothing to pip
install. This is a meaningful difference from Stage 1 and Stage 2, both of
which depend on installed packages.

---

## 5. A real reproduction blocker: hardcoded, session-specific paths

`prep_clusters.py` and `verify_grounding.py` both hardcode absolute paths
from the cloud session that actually ran them:

```python
# prep_clusters.py
STAGE2_DIR = "/home/claude/Stage2_live"
BATCHES_DIR = "/home/claude/Stage2_live/batches"
ASSIGNMENTS_CSV = os.path.join(STAGE2_DIR, "clusters", "cluster_assignments.csv")

# verify_grounding.py
BATCHES_DIR = "/home/claude/Stage2_live/batches"
ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"
```

**This is now documented directly in each script's own module docstring**
(a "HARDCODED PATH NOTICE" section was added to both files this session,
mirroring the treatment already applied to Stage 2's `embed_reviews.py` and
`cluster_categories.py`), with an inline comment above each path variable.

Both scripts will fail immediately on another machine until these lines are
edited. Based on what each script reads:

- `BATCHES_DIR` must point at a folder of `batch_*.csv` files with columns
  `review_id_hash, review_text` — the same folder `stage2_clustering/`'s
  scripts need (see that stage's documentation for the exact source: your
  `stage1_classification/full_corpus_classifier/batches/` folder).
- `ASSIGNMENTS_CSV` must point at Stage 2's `cluster_assignments.csv` (your
  `stage2_clustering/clusters/cluster_assignments.csv`, independently
  verified in that stage's documentation to have 67,300 rows / 58,388
  non-noise).

`merge_outputs.py`, `merge_ratings.py`, `investigate_flags.py`, and
`human_rate_stage3.py` have no hardcoded external paths — they only
reference files inside this same folder (`HERE = os.path.dirname(...)`),
so they run correctly wherever this folder is placed.

---

## 6. End-to-end reproduction steps

### 6.1 One-time setup
- Install Python 3.11+. No packages to install.
- Ensure an environment with subagent-dispatch capability for the two LLM
  steps (generation and rating) — this is not a scripted API call you can
  run unattended the way Stage 1's classification is.
- Edit the two path lines described in §5 in `prep_clusters.py` and
  `verify_grounding.py`.

### 6.2 Step 1 — Prep (`prep_clusters.py`)
- Run `python3 prep_clusters.py`. Joins every non-noise cluster's review IDs
  to full review text, samples down to 150 (seed 42) if larger, splits into
  50-review chunks if the (possibly sampled) set exceeds that.
- Expect console output reporting: reviews loaded, non-noise clusters found,
  prep files written, missing-text count (should be 0), and counts of
  clusters requiring sampling/chunking.
- Output: `prep/<CATEGORY>__<cluster_id>.json` × 77, plus `prep_manifest.json`.

### 6.3 Step 2 — Generation (6 parallel LLM subagents)
- Not a script — an interactive step. Assign the 77 clusters to 6 groups
  (balanced by chunk count), and dispatch one subagent per group, each given
  its assigned clusters' full prep data and instructed to: never state a
  proportion without having counted it in the sample; quote only verbatim
  text with real review IDs; disclose ambiguity or redundancy with
  neighboring clusters. See §7 for the fuller instruction set this run
  followed.
- Output: `outputs/group1.json`…`group6.json`.

### 6.4 Step 3 — Merge + completeness check (`merge_outputs.py`)
- Run `python3 merge_outputs.py`. Merges the 6 group files, normalizes
  `cluster_id` to string, checks for duplicates/missing/extra against
  `prep_manifest.json`. Expect `PASSED` with 0/0/0.
- Output: `stage3_roadmap_items.json` / `.csv`.

### 6.5 Step 4 — Independent grounding verification (`verify_grounding.py`)
- Run `python3 verify_grounding.py`. Re-checks every quote from scratch
  against the full corpus and the real cluster assignments — not the
  sampled subset a subagent saw. Confirms each `review_id` exists, belongs
  to the claimed (category, cluster), and is an exact whitespace-normalized
  substring of that review's real text.
- Output: `grounding_check_report.json`.

### 6.6 Step 5 — Blind adversarial rating (6 fresh LLM subagents) + merge (`merge_ratings.py`)
- Dispatch a second, independent set of 6 subagents — with no memory of the
  generation step — using the same group assignments, instructed to read
  the entire sampled review set for each cluster and rate
  faithfulness/clarity/usefulness (1–5) with free-text notes.
- Run `python3 merge_ratings.py` to merge, check completeness, and compute
  aggregate + per-category stats.
- Output: `ratings/group1_ratings.json`…`group6_ratings.json`,
  `stage3_ratings.json`, `stage3_ratings_summary.json`.

### 6.7 Step 6 — Investigate and correct flagged items (`investigate_flags.py`)
- Filter the rating pass's free-text notes to substantive faithfulness
  problems (not usefulness/redundancy notes). For each flagged item,
  independently re-read the actual sampled review text in `prep/` and, if a
  proportion is in question, recompute it from scratch — do not accept a
  rating subagent's characterization as fact. `investigate_flags.py` shows
  exactly how this run did that recomputation and is rerunnable.
- Correct confirmed issues directly in the data: mark `corrected: true`,
  add a `correction_note`, preserve a pre-correction backup
  (`stage3_roadmap_items.json.bak_pre_fix`).
- Re-run Step 4 (`verify_grounding.py`) against the corrected file to
  confirm the fix didn't break grounding.

### 6.8 Step 7 — Human-rating tool: build, don't run (`human_rate_stage3.py`)
- Build (or reuse) a terminal tool that walks a human rater through all 77
  items blind to the AI ratings, with resume support. Smoke-test it
  (confirm it loads the roadmap file and reports the correct remaining
  count) but do not fabricate or simulate human ratings.

### 6.9 Step 8 — Write the run log
- Document every step's actual console output/counts, the full 9-item
  correction table with each item's independent evidence, the environment,
  and all limitations — as `STAGE3_RUN_LOG.md` does for this run.

### 6.10 What downstream stages actually need
Only `stage3_roadmap_items.json` (and `.csv`) is the real output consumed
downstream. Everything else in this folder (`prep/`, `outputs/`, `ratings/`,
the backup file) exists for audit and reproducibility, not because a later
stage reads it directly.

---

## 7. Exact configuration and instructions used

### 7.1 Parameters

| Setting | Value |
|---|---|
| Model (generation and rating) | Claude Sonnet 5 (`claude-sonnet-5`) |
| Sampling cap | 150 reviews per cluster (`random.Random(42)`-seeded sample for larger clusters) |
| Chunk size | 50 reviews per chunk, hierarchical map-then-reduce for larger (sampled) sets |
| Generation groups | 6, balanced by chunk count (not cluster count) |
| Rating groups | 6, same group assignments as generation, but independent subagent instances with no memory of generation |
| Quotes per item | 2–3, verbatim, with real `review_id` |

### 7.2 On "the exact prompt" — an important disclosure

Unlike Stage 1, where the literal classification prompt is a fixed string
baked into a script and reproduced exactly, Stage 3's generation and rating
steps were each executed as interactive dispatches of independent LLM
subagents within this session. **The literal, word-for-word text sent to
each of the 12 subagent dispatches (6 generation + 6 rating) in this
specific run is not preserved as a file artifact in this folder** — only a
paraphrased summary of the instructions survives, in `STAGE3_RUN_LOG.md`
§4 and §7.

What *is* available, and is the closest thing to a reproducible prompt for
this stage, is a pre-existing handoff prompt already saved in this project
(`Stage3_reproduction_prompt.md`), which specifies the same 8-step
methodology this run's log says it followed. That document is explicit
about its own limits: it is "a faithful, complete specification of what was
actually done," not a literal transcript of what was typed into any single
subagent dispatch, and it has "not itself been tested end-to-end as a
single, unattended, one-shot invocation." Treat §8 below (the handoff
prompt) as built from that same specification, with the same caveat
attached — it describes the methodology precisely, but running it is not
guaranteed to reproduce this run's exact wording, exact group assignments,
or exact flagged items.

The instructions this run's subagents were actually given, as recorded in
`STAGE3_RUN_LOG.md` (paraphrased, not verbatim):

- **Generation subagents** (§4 of the run log): given each assigned
  cluster's full prep data (every chunk, not a summary), instructed to (a)
  never state a proportion/percentage without having actually counted it in
  the sample, (b) select verbatim quotes only, with real `review_id`s, (c)
  disclose ambiguity or redundancy with neighboring clusters rather than
  papering over it.
- **Rating subagents** (§7 of the run log): no memory of the generation
  step, instructed to read the entire sampled review set for each cluster
  (not just the title/description/quotes) and independently re-derive any
  stated proportion before judging faithfulness, then score
  faithfulness/clarity/usefulness (1–5) with free-text notes.

---

## 8. A prompt you can hand an AI assistant to run this stage for you

This is adapted from `Stage3_reproduction_prompt.md` (already in this
project), with the same caveat that document attaches to itself: it is a
faithful specification of the methodology, not a confirmed one-shot recipe.
Steps 3, 4, and 6 (completeness check, independent grounding check, and
manual investigation of anything flagged) are what caught the real problems
in this run — don't skip them because the instructions are detailed.

```
Run Stage 3 (structured summarization) of the review-mining pipeline.
Input: Stage 2's non-noise cluster assignments (cluster_assignments.csv,
excluding cluster_id == -1) joined to full review text from Stage 1's
batch files.

1. Prepare. For every (category, cluster_id) pair, if the cluster has
   <=150 reviews use all of them; if more, draw a random.Random(42)-seeded
   sample of exactly 150. Split whatever set you're summarizing into
   chunks of 50 for hierarchical map-then-reduce if it exceeds 50. Write
   one JSON file per cluster and an authoritative manifest recording
   n_total/n_sampled/n_chunks per cluster -- that manifest, not your own
   later recollection, is what every completeness check below must be
   measured against.

2. Generate. For every cluster, produce a title, a 1-3 sentence
   description, and 2-3 verbatim supporting quotes with review_id, via
   parallel subagents grouped to balance workload. For every description,
   explicitly state what proportion of the sampled reviews the described
   theme actually represents, and do not imply a theme is dominant unless
   a plurality or majority of the sampled reviews actually support it --
   if the strongest available theme is a minority pattern, say so
   explicitly. For every quote, read the quoted review's full text before
   finalizing it and confirm the surrounding sentences don't reverse its
   meaning.

3. Merge and check completeness. Merge all group outputs, normalize ID
   types (don't assume they match across independently-written outputs),
   and verify zero duplicates, zero missing, zero extra against the
   manifest from step 1 before proceeding.

4. Independently verify grounding. Using a fresh script -- not by
   trusting the generating subagents' self-report -- confirm for every
   quote: (a) the review_id exists in the corpus, (b) it genuinely
   belongs to the claimed (category, cluster) per the real
   cluster-assignment file, (c) the quote is an exact, whitespace-
   normalized, contiguous substring of that review's actual text. Report
   the full pass/fail breakdown, not just a final count.

5. Rate quality, blind and adversarial. Dispatch fresh subagents with no
   memory of the generation step, instructed to be skeptical, to
   independently re-read the sampled source reviews (not just the
   written description) for every item, and to score faithfulness,
   clarity, and usefulness 1-5 with a written justification each.
   Disclose explicitly that this AI-only pass is not equivalent to
   independent human evaluation.

6. Chase every faithfulness flag down to the source, yourself. For any
   item the rating pass flags on faithfulness, do not accept the rating
   subagent's characterization as fact. Read every sampled review in that
   cluster's prep file directly, and independently confirm or refute the
   flag before touching the data. If confirmed, fix it: keep any quote
   that is genuinely accurate, replace any quote whose full source
   context reverses its meaning, rewrite the title/description to state
   the item's true proportion. Mark corrected items (a corrected flag and
   a correction_note field), preserve a pre-correction backup, and re-run
   steps 3 and 4 against the corrected file.

7. Build, but do not fabricate, a human-evaluation path. Build a terminal
   or equivalent rating tool that lets a real person score every item
   blind to the AI ratings, with the ability to pull up the real source
   reviews, and with progress saved after every entry. Do not run it
   yourself, simulate human judgments, or report placeholder scores as
   real; state plainly that it's built and smoke-tested but not yet used
   for real judgments.

8. Write it up with full source verification. Every quantitative claim
   traceable to an exact command or file, every correction disclosed with
   its full evidentiary trail, every limitation stated plainly, and no
   claim presented as confirmed that rests only on a subagent's
   self-report rather than your own independent check against the
   underlying data.

After finishing, report back: the per-group item counts, the completeness
and grounding check results, the aggregate rating scores, the full list of
corrected items with their independent evidence, and every limitation —
including that the rating pass is AI-only (same-model-family evaluators,
not independent human judgment) and that a rerun of this stage would very
likely surface a different set of faithfulness issues than this run found,
not necessarily a larger or smaller one.
```

---

## 9. Known gaps and disclosed limitations

- **No literal, verbatim record of the exact subagent prompts used in this
  run** (§7.2) — only a paraphrased instruction summary in
  `STAGE3_RUN_LOG.md` and a pre-existing methodology specification
  (`Stage3_reproduction_prompt.md`) survive. This is a real gap relative to
  Stage 1, where the exact prompt string is reproducible from a script.
- **Hardcoded, non-portable paths** in `prep_clusters.py` and
  `verify_grounding.py` (§5) — now flagged in each script's own docstring
  with an inline comment above each path variable, but still requires
  manual editing before either script will run on a different machine.
- **The rating pass is AI-only.** Six fresh same-model-family subagents
  rated the outputs; this is explicitly not a substitute for independent
  human evaluation. `human_rate_stage3.py` is the disclosed, built-but-unused
  upgrade path.
- **The 150-review sampling cap limits coverage of large clusters** — a
  theme occurring only in the unsampled portion of a large cluster cannot
  influence that item. Most pronounced for `GENERAL_SENTIMENT` cluster 3
  (150 of 7,740 reviews sampled, ≈1.9%).
- **The 9 corrections were made by direct human-style re-reading in this
  session, not by re-running generation** — deliberately, to avoid
  compounding one AI-authored error with an unaudited AI-authored "fix."
  This means the corrections reflect this session's own judgment calls on
  exact wording, which a human domain expert might phrase differently even
  while agreeing on the underlying facts.
- **This run's investigation covered the 9 items flagged by the rating
  pass**, not all 77 — the correction process does not establish that the
  remaining 68 items are error-free, only that the specific issues flagged
  by the adversarial rating pass were checked and, where genuine, fixed.
- **Redundancy across near-duplicate clusters** (e.g., `SECURITY_PRIVACY`
  clusters 2/5/6/7/8/9 all describing variations of "hacked account, no
  reimbursement") was disclosed in the affected items' descriptions but not
  resolved by merging or restructuring clusters — that would be a Stage 2
  parameter-tuning decision, out of scope for this stage.
- **Clustering upstream of this stage is itself non-deterministic**
  (UMAP's stochasticity — see `stage2_clustering/`'s documentation), so a
  rerun of the whole pipeline is not expected to reproduce this exact set
  of 77 clusters, let alone the same 9 flagged items.

---

## 10. Time summary

| Step | Started (this run, UTC) |
|---|---|
| Prep | 2026-09-24 16:23:29 |
| Generation (6 parallel agents) | ~16:23–16:29 |
| Merge outputs | 2026-09-24 16:30:25 |
| Grounding check (pre-correction) | 2026-09-24 16:30:38 |
| Blind rating (6 parallel agents) | ~16:30–16:37 |
| Merge ratings | ~16:43 |
| Independent investigation + correction of 9 flags | ~16:50–17:10 |
| Grounding check (post-correction) | ~17:10 |
| Human-rating tool built + smoke-tested | ~17:12 |

No dollar cost tracked separately for this stage in the available logs —
the generation/rating steps run through the same subagent-dispatch
mechanism as this session's own tool use rather than a separately billed
API call.

---

*Everything above marked "✅ verified this session" was checked by directly
opening and recomputing from the actual files in `stage3_summarization/` as
connected to this session on 2026-09-30 — sampling totals, completeness
counts, the 9-item correction table, and rating distributions were computed
fresh from `prep_manifest.json`, `stage3_roadmap_items.json`, and
`stage3_ratings.json` themselves, not copied from the folder's own README or
log claims.*
