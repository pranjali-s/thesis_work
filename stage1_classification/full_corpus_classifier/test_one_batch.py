"""
Cheap sanity check — run this BEFORE re-running classify_reviews.py on all
160 remaining batches.

It sends ONE batch (default: batch 016) as a normal synchronous API call
(not the async Batches API — for a single request that's simpler and gives
you an answer in seconds instead of waiting on a batch job), with thinking
explicitly disabled, and tells you immediately whether it comes back with a
real, correctly-formatted, complete answer.

Expected cost: well under 5 cents (roughly 12k input + 4k output tokens at
STANDARD, non-batch rates — this one test isn't worth the batch-job setup
just to save the 50% discount on a few cents).

Run:
    python3 test_one_batch.py
    python3 test_one_batch.py 42      # test a different batch number
"""

import csv
import os
import sys

from anthropic import Anthropic

import config
from classify_reviews import build_batches, build_request, parse_response_text, verify

STANDARD_INPUT_RATE = 2.0 / 1_000_000   # claude-sonnet-5 standard (non-batch) rate
STANDARD_OUTPUT_RATE = 10.0 / 1_000_000


def main():
    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 16

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY first.")
    client = Anthropic(api_key=api_key)

    batch_paths = build_batches()
    if batch_num not in batch_paths:
        raise SystemExit(f"batch {batch_num} doesn't exist (1-{len(batch_paths)})")

    with open(batch_paths[batch_num], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    req = build_request(batch_num, rows)
    print(f"Sending batch {batch_num:03d} ({len(rows)} reviews) as a single synchronous call...")

    message = client.messages.create(**req["params"])

    print(f"stop_reason: {message.stop_reason}")
    print(f"input_tokens: {message.usage.input_tokens}  output_tokens: {message.usage.output_tokens}")
    cost = (message.usage.input_tokens * STANDARD_INPUT_RATE
            + message.usage.output_tokens * STANDARD_OUTPUT_RATE)
    print(f"cost of this one test call (standard rate): ${cost:.4f}")

    text = "".join(block.text for block in message.content if block.type == "text")
    print(f"\n--- first 5 lines of response ---")
    for line in text.strip().splitlines()[:5]:
        print(line)
    print("--- last 5 lines of response ---")
    for line in text.strip().splitlines()[-5:]:
        print(line)

    parsed = parse_response_text(text, rows)
    out_path = f"/tmp/test_batch_{batch_num:03d}_result.csv" if os.name != "nt" else f"test_batch_{batch_num:03d}_result.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["review_id_hash", "labels"])
        w.writeheader()
        w.writerows(parsed)

    v = verify(batch_paths[batch_num], out_path)
    print(f"\nverification result: {v}")
    if v["ok"]:
        print("\n✅ SUCCESS — thinking-disabled fix works. Safe to re-run classify_reviews.py for the full remaining batches.")
    else:
        print("\n❌ Still failing — do not run the full job yet, send me this output.")


if __name__ == "__main__":
    main()
