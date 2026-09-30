# Stage 1 (LLM-Based Classification) — Full Documentation

**Verified file inventory, recomputed results, and reproduction guide.**
Everything under "verified this session" was checked directly against the
files connected in `stage1_classification/` on 2026-09-30 — row counts,
ID-set matches, label vocabulary, manifest status, and all three
reliability tables were recomputed from raw data, not copied from any
README's own claims. Where a claim in the thesis text or the project's
fuller `Stage1_4.4.1_writeup.md` could **not** be re-verified from what's
connected here, that is stated explicitly rather than assumed to still
hold.

---

## 1. What this folder is

Stage 1 (thesis §5.1 / internal write-up §4.4.1): LLM-based multi-label
classification of the 52,392-review corpus against the 17-code taxonomy,
using `claude-sonnet-5` via the Anthropic Messages Batches API. Three
subfolders:

| Subfolder | What it does | Rows | Status |
|---|---|---|---|
| `full_corpus_classifier/` | Classifies the entire 52,392-review corpus (175 batches) | 52,392 | ✅ Complete, verified |
| `ground_truth_classification/` | Classifies the 5,544 ground-truth reviews not in the 616-review reliability subsample | 5,544 | ✅ Complete, verified |
| `human_review_tool/` | Keyword-baseline classifier over the 616-review subsample (the human-coding tool exists but was never used — see §6) | 616 | ✅ Keyword baseline complete; human coding never run (by design, not by gap) |

---

## 2. Verified file inventory

### 2.1 `full_corpus_classifier/`

| File | Verified this session |
|---|---|
| `combined_reviews.csv` | ✅ 52,392 rows, 52,392 unique `review_id_hash` |
| `stage1_full_corpus_labels.csv` | ✅ 52,392 rows, ID set **exactly matches** the corpus (0 missing, 0 extra), 0 empty labels, 0 invalid-vocabulary labels |
| `manifest.json` | ✅ 175/175 batches `verified_done`. `total_reviews: 53275` confirmed to be the sum of batch-file physical line counts, not unique reviews — a disclosed counting artifact, not a data problem |
| `classify_reviews.py`, `config.py`, `verify_combined.py`, `diagnose_batch.py`, `test_one_batch.py`, `requirements.txt` | ✅ Present |
| `batches/`, `results/` (175 each) | ✅ All 175 present in both |
| `test_batch_016_result.csv` | ✅ Present |

### 2.2 `ground_truth_classification/`

| File | Verified this session |
|---|---|
| `remaining_ground_truth.csv` | ✅ 5,544 rows, 5,544 unique IDs, **disjoint** from the 616-review subsample, **subset** of the full corpus |
| `step6_ground_truth_labels.csv` | ✅ 5,544 rows, ID set **exactly matches** `remaining_ground_truth.csv` |
| `manifest.json` | ✅ 19/19 batches `verified_done`. `total_reviews: 5653` — same counting artifact as above |
| `classify_reviews.py`, `config.py`, `verify_combined.py`, `requirements.txt` | ✅ Present |

**Union check (independently recomputed):** the 616-review subsample and
the 5,544-review remainder are disjoint, and their union is exactly
6,160 reviews — all a subset of the 52,392-review corpus. This matches
the thesis's stated ground-truth frame size.

### 2.3 `human_review_tool/`

| File | Verified this session |
|---|---|
| `B4_human_reliability_subsample_v2.csv` | ✅ 616 rows, 616 unique IDs. `source_tag`: 456 `base` + 40 each of 4 booster categories (SECURITY_PRIVACY, ASSET_COVERAGE, PREDICTION_MARKETS, ACCOUNT_LIFECYCLE) = 616 |
| `keyword_baseline_labels.csv` | ✅ 616 rows, ID set **exactly matches** the 616-review subsample |
| `human_code.py` | ✅ Present (built, tested, never used to code any reviews — see §6) |
| `README.md` | ✅ Present |

**Not present in this folder**, confirmed by direct listing:
`human_coding_results.csv` (expected — see §6, this was a deliberate
methodology change, not an incomplete step) and two files needed to
**independently re-verify Tables 5.2 and 5.3** — see §3.2 and §5.

---

## 3. Verified results, recomputed fresh

### 3.1 Table 5.1 — full-corpus label frequencies (n = 52,392): ✅ exact match

Recomputed directly from `stage1_full_corpus_labels.csv`: 52,392 rows,
ID set exactly equal to the corpus, 0 empty labels, 0 invalid codes, mean
**1.2845** labels/review (75.9% one code, 20.1% two, 3.7% three, 0.3%
four or more). Every one of the 17 per-code counts/percentages in the
thesis's Table 5.1 reproduced exactly — e.g. GENERAL_SENTIMENT 17,435
(33.3%), USABILITY_NAV 12,247 (23.4%), down to PREDICTION_MARKETS 303
(0.6%). No discrepancy found.

### 3.2 Tables 5.2 and 5.3 (reliability checks): ⚠️ cannot be independently recomputed from this connected folder

Both tables depend on a file called `ai_labels_616.csv` — a **separate**
LLM classification of the 616-review subsample, run independently of the
main 52,392-review corpus pass (per the project's `Stage1_4.4.1_writeup.md`
§4.4.1.8, it was generated "directly within the researcher's interactive
session," not through the Batches API script). This file is **not present**
anywhere in the currently connected `stage1_classification/` folder — a
targeted search of the whole tree found no file matching `ai_labels*`,
`ground_truth_6160*`, or `step8*`.

What this means concretely:

- **Table 5.2** (keyword baseline vs. LLM, n=616): the keyword-baseline
  half (`keyword_baseline_labels.csv`) is present and ID-verified. The
  "LLM classifier" half (`ai_labels_616.csv`) is missing, so the 41.6%
  exact-match / 0.535 Jaccard / per-category kappa figures **cannot be
  recomputed from what's connected here**.
- **Table 5.3** (test-retest, n=6,160): the "run 2" side needs
  `ai_labels_616.csv` (616) + `step6_ground_truth_labels.csv` (5,544).
  The second file is present and verified; the first is missing, so the
  79.1% exact-match / 0.860 Jaccard / per-category kappa figures likewise
  **cannot be recomputed from what's connected here**.

This is **not** a sign the numbers are wrong. The project's own
`Stage1_4.4.1_writeup.md` (§4.4.1.11) documents having independently
recomputed both tables previously, cell-for-cell, against
`ai_labels_616.csv` and an `evaluation/` folder (`ai_ground_truth_6160.csv`,
`step8_stage1_vs_groundtruth_results.txt`) — neither of which is in the
folder connected to this session. The numbers in the thesis document the
user provided match that write-up exactly. But as connected right now,
this folder cannot reproduce Tables 5.2/5.3 on its own — only Table 5.1.
If `ai_labels_616.csv` and the `evaluation/` folder can be located and
connected, both tables become independently re-verifiable the same way
Table 5.1 was.

### 3.3 Manifest / batch integrity: ✅ verified

Both `manifest.json` files opened directly: 175/175 and 19/19 batches
`status: verified_done`. The inflated `total_reviews` fields (53,275 vs.
52,392; 5,653 vs. 5,544) were confirmed to equal the sum of each batch
file's physical line count — reviews with embedded newlines span more
than one physical line — not a count of unique reviews. This matches the
folder's own disclosed explanation exactly.

---

## 4. Environment

| Setting | Value |
|---|---|
| Model | `claude-sonnet-5` |
| API | Anthropic Message Batches API (async, 50% of standard price) |
| Extended thinking | Disabled (`"thinking": {"type": "disabled"}`) — required, see §6 |
| `max_tokens` | 8,192 per request |
| Batch size | 300 reviews/request |
| Shuffle seed | 42 (fixed) |
| Python package | `anthropic>=0.40.0` (original env: 1.6.0) |
| Python version | 3.9+ (original run used 3.14 per `__pycache__`; nothing 3.14-specific) |

---

## 5. Reproduction blockers (what a fresh session would need beyond this folder)

1. **`ai_labels_616.csv`** — the independent 616-review LLM reclassification. Without it, Tables 5.2 and 5.3 cannot be recomputed (see §3.2). Not a script output reproducible by re-running anything in this folder; it was generated by direct in-session model calls, not the batch script.
2. **`evaluation/ai_ground_truth_6160.csv`** and **`evaluation/step8_stage1_vs_groundtruth_results.txt`** — the merged comparison file and computed output backing Table 5.3, per `Stage1_4.4.1_writeup.md` §4.4.1.11.
3. **`B4_ground_truth_frame_v2.csv`** — the single combined 6,160-row sampling frame file. Its properties (616+5,544 disjoint union) are independently reconstructable from the two component files present here, so this is a lower-priority gap than #1–2.
4. An **Anthropic Console API key** (separate from a claude.ai subscription) for re-running either classification script.
5. A **live corpus file** (`combined_reviews.csv`) matching the review-collection step's output, if reclassifying from scratch rather than reusing what's here.

---

## 6. What actually happened methodologically (so the reproduction steps make sense)

The 616-review subsample was originally reserved for **human coding**
against the taxonomy, to support a genuine inter-rater reliability
estimate. A terminal tool (`human_code.py`) was built and tested for
this. Under a disclosed time constraint, the researcher chose full
keyword automation instead — a deterministic keyword/phrase classifier
was built from the taxonomy definitions and applied to all 616 reviews
with no human check. This is why `human_coding_results.csv` does not
exist: it isn't a missed step, it's a deliberate, disclosed departure
from the original design. Because of this, Table 5.2 measures
**keyword-vs-LLM concordance**, not inter-rater reliability, and Table
5.3 measures the classifier's **test-retest consistency against itself**
(a second independent run), not validity against ground truth. Neither
table should be read as an accuracy or validation claim — both the
thesis document and the project's fuller write-up already state this
explicitly.

---

## 7. End-to-end reproduction steps

1. `cd full_corpus_classifier && pip install -r requirements.txt && export ANTHROPIC_API_KEY=sk-ant-...`
2. Optional: `python3 test_one_batch.py` — cheap sanity check; confirm `stop_reason: end_turn`, not `max_tokens` (see the cost-incident note in §9).
3. `python3 classify_reviews.py` — rebuilds 175 batches (seed 42), submits pending ones as one Batches API job, polls, verifies, writes `stage1_full_corpus_labels.csv`.
4. `python3 verify_combined.py` — must print `PASSED`.
5. `cd ../ground_truth_classification && python3 classify_reviews.py && python3 verify_combined.py` — same process against `remaining_ground_truth.csv` (5,544 rows), writing `step6_ground_truth_labels.csv`.
6. `cd ../human_review_tool && python3 keyword_baseline_classify.py` — deterministic, regenerates `keyword_baseline_labels.csv`.
7. To reproduce Tables 5.2/5.3: independently classify the same 616 reviews a second time (direct model calls, not the batch script, per §6), save as `ai_labels_616.csv`, then compute exact-match rate, mean Jaccard, and per-category Cohen's κ against (a) `keyword_baseline_labels.csv` for Table 5.2, and (b) the original run's labels for the 6,160-review frame (616 + 5,544) for Table 5.3.

---

## 8. A prompt you can hand an AI assistant to run this stage

```
You are reproducing Stage 1 (LLM-based classification) of a retail-
trading-app review-mining pipeline. The stage1_classification/ folder
contains full_corpus_classifier/, ground_truth_classification/, and
human_review_tool/.

1. In full_corpus_classifier/: confirm combined_reviews.csv has 52,392
   rows with unique review_id_hash. Install requirements, set
   ANTHROPIC_API_KEY, run classify_reviews.py then verify_combined.py.
   Confirm PASSED and that stage1_full_corpus_labels.csv has exactly
   52,392 rows, ID set matching the corpus exactly, no empty labels, no
   codes outside the 17-code vocabulary. Re-check this yourself — do not
   trust the script's own summary line alone (it has a known line-count
   vs. row-count discrepancy in total_reviews, disclosed in the README).

2. In ground_truth_classification/: same process against
   remaining_ground_truth.csv (5,544 rows) -> step6_ground_truth_labels.csv.

3. In human_review_tool/: run keyword_baseline_classify.py (deterministic,
   already done but safe to re-run). Do NOT fabricate or simulate human
   coding — human_coding_results.csv intentionally does not exist; the
   final methodology uses keyword-baseline concordance instead (see the
   folder's README for why).

4. For the two reliability tables (keyword-vs-LLM concordance on 616
   reviews; test-retest consistency on the 6,160-review frame), you need
   a SECOND, independent classification of the 616-review subsample
   (direct model calls, same taxonomy/prompt, not the batch script) plus
   the original full-corpus run's labels for the same 6,160 IDs. Compute
   exact multi-label match rate, mean Jaccard similarity, and per-category
   Cohen's kappa for both comparisons. Report both explicitly as
   concordance/reproducibility checks, not accuracy or validity claims —
   no independent human ground truth exists anywhere in this chain.

5. Report back: full-corpus label frequencies and mean labels/review;
   both manifests' verified_done counts; any row-count or ID-set
   mismatches found; and which of the two reliability tables you could
   or could not reproduce and why.

Do not change the model, taxonomy, batch size, or the disabled-thinking
setting — see the folder's README for the cost incident this fixed.
```

---

## 9. Known gaps and disclosed limitations

- **Tables 5.2 and 5.3 cannot be independently recomputed from this connected folder** — `ai_labels_616.csv` and the `evaluation/` outputs are not present (§3.2, §5). This is the main open item.
- **`human_coding_results.csv` does not exist by design**, not by omission — the final methodology uses a keyword baseline instead of human coding, a disclosed, deliberate choice (§6).
- **`total_reviews` in both `manifest.json` files is inflated** (53,275 vs. 52,392; 5,653 vs. 5,544) — a physical-line-counting artifact, not a data problem. Confirmed this session.
- **A real cost incident is disclosed in the README:** the first full-corpus attempt spent $8.87 on 160 batches producing no usable output because Claude Sonnet 5's adaptive thinking (on by default) consumed the entire token budget. Fixed by disabling thinking; confirmed via a single test batch before the corrected run.
- **Mixed execution mechanisms, disclosed:** batches 1–15 (4,500 reviews) of the full-corpus run went through subagent dispatch inside an interactive session; batches 16–175 (47,892 reviews) and the entire ground-truth run went through the direct Messages Batches API script. Same model, taxonomy, and verification in both — only the invocation mechanism differs. **This is not disclosed in the thesis paragraph the user provided** — see §10.
- **Labels are not bit-for-bit reproducible.** LLM output is not fully deterministic; a rerun may assign slightly different labels to some reviews, and `claude-sonnet-5` could be retired or updated in the future.
- **No independent human-verified ground truth exists anywhere in this evaluation chain.** Both reliability checks compare the classifier to a cruder automated instrument or to itself — never to an external, human-checked standard.

---

## 10. Thesis-text cross-check

The document provided for this check states: *"Classification of the
52,392-review corpus was carried out through the Anthropic Messages
Batches API using Claude Sonnet 5."* This is accurate for 47,892 of the
52,392 reviews (batches 16–175) but omits that the first 4,500 reviews
(batches 1–15) were classified via a different mechanism — subagent
dispatch inside an interactive session, not the Messages Batches API —
before the pipeline switched to the direct-API script for cost reasons.
The model, taxonomy, and verification were identical either way, so this
doesn't affect any reported number, but as worded the sentence implies a
single uniform execution path for the whole corpus, which isn't quite
what happened. This is the thesis author's call to adjust or leave as
is — it wasn't edited here since the source text isn't a file directly
editable from this session.

Everything else in the provided document — Table 5.1's exact figures,
the 616/6,160 sample sizes, the 41.6%/0.535 and 79.1%/0.860 headline
reliability figures, and the Crypto-Specific Functionality boundary-case
discussion — matches the project's fuller `Stage1_4.4.1_writeup.md`
exactly, which in turn matches what's independently verifiable from this
folder wherever the underlying files are present (Table 5.1 fully;
Tables 5.2/5.3 not re-verifiable here, see §3.2).

---

## 11. Verification note

Everything above marked "✅ verified this session" was checked by
directly opening and cross-computing the actual files connected in
`stage1_classification/` on 2026-09-30 — row counts, ID-set differences,
label frequencies, and manifest status were computed fresh with Python,
not copied from any README's own claims. Table 5.1 was independently
reproduced to the same precision as the thesis document. Tables 5.2 and
5.3 were not independently reproduced because their required source
files are not present in this connected folder; this is stated as a
completeness gap in the current folder, not as doubt about the figures
themselves, which match the project's own more detailed prior write-up
exactly.
