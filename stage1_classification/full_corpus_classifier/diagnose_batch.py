"""
Diagnostic script — run this BEFORE re-running classify_reviews.py.

It re-fetches the results of the batch job you already submitted and paid
for (msgbatch_01XsVYAJJ55evLWfyp8SMYBA) WITHOUT submitting anything new —
retrieving results from an already-completed batch costs nothing further,
you already paid for the generation itself. This will not spend any more
money.

It will:
  1. Print the REAL total input/output tokens and REAL cost for that job
     (replacing my earlier estimate with ground truth).
  2. Print each result's stop_reason (tells us if responses were being
     cut off by the max_tokens cap — likely culprit).
  3. Save the full raw text of a few sample responses to
     diagnostics/batch_016_raw.txt etc. so we can see exactly what format
     the model actually used.
  4. Print a quick format-match count (how many lines look like
     "<digit>|<CODE>" vs how many don't) for those samples.

Run:
    python3 diagnose_batch.py
"""

import os
import csv

from anthropic import Anthropic

import config

BATCH_ID = "msgbatch_01XsVYAJJ55evLWfyp8SMYBA"  # the job from your run
SAMPLE_BATCHES_TO_SAVE = {16, 18, 73, 175}  # first, and a couple of the worst-looking ones

# Batch API pricing for claude-sonnet-5 (as of 2026-09-18): $1/MTok in, $5/MTok out
BATCH_INPUT_RATE = 1.0 / 1_000_000
BATCH_OUTPUT_RATE = 5.0 / 1_000_000


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY first.")
    client = Anthropic(api_key=api_key)

    os.makedirs("diagnostics", exist_ok=True)

    total_in = 0
    total_out = 0
    stop_reason_counts = {}
    n_results = 0
    format_match_total = 0
    format_line_total = 0

    for result in client.messages.batches.results(BATCH_ID):
        n_results += 1
        custom_id = result.custom_id
        batch_num = int(custom_id.split("_")[1])

        if result.result.type != "succeeded":
            print(f"batch {batch_num:03d}: NOT succeeded -> {result.result.type}")
            continue

        message = result.result.message
        usage = message.usage
        total_in += usage.input_tokens
        total_out += usage.output_tokens

        sr = message.stop_reason
        stop_reason_counts[sr] = stop_reason_counts.get(sr, 0) + 1

        text = "".join(block.text for block in message.content if block.type == "text")

        # quick format check
        lines = [l for l in text.strip().splitlines() if l.strip()]
        pipe_lines = [l for l in lines if "|" in l]
        digit_pipe_lines = [l for l in pipe_lines if l.split("|", 1)[0].strip().isdigit()]
        format_line_total += len(lines)
        format_match_total += len(digit_pipe_lines)

        if batch_num in SAMPLE_BATCHES_TO_SAVE:
            out_path = f"diagnostics/batch_{batch_num:03d}_raw.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"stop_reason: {sr}\n")
                f.write(f"input_tokens: {usage.input_tokens}  output_tokens: {usage.output_tokens}\n")
                f.write(f"total lines: {len(lines)}  pipe lines: {len(pipe_lines)}  digit|pipe lines: {len(digit_pipe_lines)}\n")
                f.write("-" * 60 + "\n")
                f.write(text)
            print(f"Saved raw response for batch {batch_num:03d} -> {out_path}")

    print("\n=== SUMMARY ===")
    print(f"results returned: {n_results}")
    print(f"stop_reason counts: {stop_reason_counts}")
    print(f"total input tokens:  {total_in:,}")
    print(f"total output tokens: {total_out:,}")
    real_cost = total_in * BATCH_INPUT_RATE + total_out * BATCH_OUTPUT_RATE
    print(f"REAL cost for this job (batch-rate pricing): ${real_cost:.2f}")
    if format_line_total:
        print(f"format check: {format_match_total}/{format_line_total} lines matched '<digit>|CODE' pattern "
              f"({100*format_match_total/format_line_total:.1f}%)")
    print("\nOpen the files in diagnostics/ and paste a snippet back — that'll tell us exactly "
          "what format the model used so I can fix the parser before you spend anything else.")


if __name__ == "__main__":
    main()
