# Step 6 — AI classifier on the remaining ~5,544 ground-truth reviews

This is the same pipeline you already ran successfully for Stage 1
(`classify_reviews.py`, direct Anthropic Messages Batches API calls),
pointed at a different, much smaller input: the 5,544 ground-truth
reviews not already covered by the 616-review reliability subsample
(steps 4-5, already done). It includes the fix from last time —
`"thinking": {"type": "disabled"}` — so you should NOT hit the
stop_reason=max_tokens problem from the first Stage 1 attempt.

## Cost estimate

19 batches (18 of 300 reviews + 1 of 144). Based on the real, measured
per-batch cost from your corrected Stage 1 run (~$0.043–0.086/batch via
the Batches API), expect roughly **$0.75–1.20 total** — comfortably
within your remaining ~$3 balance, with room to spare even if a batch or
two needs a retry.

## How to run it

1. Same setup as before: `pip install -r requirements.txt`, then
   `export ANTHROPIC_API_KEY=sk-ant-...` (reuse the same key from Stage 1).
2. `python3 classify_reviews.py`
   - Rebuilds 19 batches from `remaining_ground_truth.csv` (already
     included in this folder — nothing to point at your own corpus for
     this one).
   - Submits all 19 as one Batches API job, polls until done, verifies
     each batch (same 4 checks as always), writes
     `step6_ground_truth_labels.csv`.
3. Once it says all batches are verified-done, run
   `python3 verify_combined.py` for the final independent check (row
   count + exact ID match against `remaining_ground_truth.csv`).
4. Send `step6_ground_truth_labels.csv` back and I'll combine it with the
   616-review AI labels from steps 4-5 into the full ~6,160-review ground
   truth, then move to step 8 (evaluating the Stage 1 full-corpus output
   against it).

If anything fails verification, just re-run `python3 classify_reviews.py`
— it only resubmits batches that aren't yet verified-done, same as before.
