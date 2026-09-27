"""
Stage 1 full-corpus classification — direct Anthropic API version.

WHY THIS SCRIPT EXISTS
-----------------------
Batches 1-15 (4,500 reviews) were classified by dispatching one general-
purpose subagent per batch inside an orchestration harness. That worked and
every batch passed independent verification, but each subagent call burned
95,000-132,000 tokens per 300-review batch — mostly harness overhead (its
own tool calls, reasoning, retries), not the ~10-15k tokens the
classification task itself needs. This script does the exact same
classification task (same model, same taxonomy, same multi-label format,
same independent verification) with one direct Message Batches API call per
batch instead of a subagent, which removes essentially all of that
overhead and gets you the Batches API's 50% price discount on top.

Nothing about the METHODOLOGY changes: same model (claude-sonnet-5), same
17-code taxonomy, same multi-label pipe-delimited output, same
per-batch independent verification (row count / id-set / label-vocabulary /
no-empty-labels) that batches 1-15 were held to. Only the execution
mechanism changes.

WHAT THIS SCRIPT DOES
----------------------
1. Reads your local corpus CSV and rebuilds the same 175 batches of 300
   reviews using the same seed=42 shuffle as the original run, so batch
   numbering lines up exactly with the already-completed batches 1-15
   (shipped in results/).
2. Skips any batch whose result file already exists and passes
   verification (so batches 1-15 are skipped automatically).
3. Submits every remaining pending batch as ONE Anthropic Message Batches
   API job (each batch of 300 reviews = one request in the job).
4. Polls the job until Anthropic reports it finished (can take up to 24h
   per Anthropic's own SLA, though it is normally much faster).
5. Retrieves results, parses them back into per-review labels, WRITES each
   batch's result CSV, and independently re-verifies it against the batch's
   input file (the same four checks used throughout this project) before
   marking it done in manifest.json.
6. At the end, concatenates every verified batch's results into one
   combined CSV covering the whole corpus.

HOW TO RUN THIS
-----------------
See README.md for the full step-by-step guide. Short version:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 classify_reviews.py
"""

import csv
import json
import os
import random
import sys
import time

import config

try:
    from anthropic import Anthropic
except ImportError:
    print("Missing dependency. Run: pip install -r requirements.txt")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Step 1: rebuild the 175 batches deterministically from the local corpus
# ---------------------------------------------------------------------------

def build_batches():
    with open(config.CORPUS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit(f"No rows read from {config.CORPUS_CSV} — check the path in config.py")

    rng = random.Random(config.SHUFFLE_SEED)
    rng.shuffle(rows)

    os.makedirs(config.BATCHES_DIR, exist_ok=True)
    n_batches = (len(rows) + config.BATCH_SIZE - 1) // config.BATCH_SIZE
    batch_paths = {}
    for i in range(n_batches):
        batch_num = i + 1
        chunk = rows[i * config.BATCH_SIZE:(i + 1) * config.BATCH_SIZE]
        path = os.path.join(config.BATCHES_DIR, f"batch_{batch_num:03d}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["review_id_hash", "app", "platform", "review_text"])
            w.writeheader()
            for r in chunk:
                w.writerow({
                    "review_id_hash": r["review_id_hash"],
                    "app": r["app"],
                    "platform": r.get("platform", ""),
                    "review_text": r["review_text"],
                })
        batch_paths[batch_num] = path

    print(f"Rebuilt {n_batches} batches ({len(rows)} reviews total, seed={config.SHUFFLE_SEED}).")
    return batch_paths


# ---------------------------------------------------------------------------
# Step 2: verification (ported from verify_batch.py, unchanged logic)
# ---------------------------------------------------------------------------

def verify(batch_input_path, batch_output_path):
    errors = []
    with open(batch_input_path, newline="", encoding="utf-8") as f:
        input_ids = [r["review_id_hash"] for r in csv.DictReader(f)]
    input_set = set(input_ids)
    if len(input_ids) != len(input_set):
        errors.append(f"INPUT has duplicate ids (unexpected): {len(input_ids)} rows, {len(input_set)} unique")

    try:
        with open(batch_output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            out_rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        return {"ok": False, "errors": [f"output file not found: {batch_output_path}"]}

    if fieldnames is None or "review_id_hash" not in fieldnames or "labels" not in fieldnames:
        errors.append(f"bad header: {fieldnames}")
        return {"ok": False, "errors": errors}

    if len(out_rows) != len(input_ids):
        errors.append(f"row count mismatch: input={len(input_ids)} output={len(out_rows)}")

    out_ids = [r["review_id_hash"] for r in out_rows]
    out_id_set = set(out_ids)
    if len(out_ids) != len(out_id_set):
        errors.append(f"output has duplicate review_id_hash: {len(out_ids)} rows, {len(out_id_set)} unique")

    missing = input_set - out_id_set
    extra = out_id_set - input_set
    if missing:
        errors.append(f"missing {len(missing)} ids from output, e.g. {list(missing)[:5]}")
    if extra:
        errors.append(f"output has {len(extra)} ids not in input, e.g. {list(extra)[:5]}")

    bad_label_rows = 0
    empty_label_rows = 0
    for r in out_rows:
        labels_raw = (r.get("labels") or "").strip()
        if not labels_raw:
            empty_label_rows += 1
            continue
        labels = [l.strip() for l in labels_raw.split("|") if l.strip()]
        if not labels:
            empty_label_rows += 1
            continue
        for l in labels:
            if l not in config.VALID_CODES:
                bad_label_rows += 1
                break
    if empty_label_rows:
        errors.append(f"{empty_label_rows} rows have empty/no labels")
    if bad_label_rows:
        errors.append(f"{bad_label_rows} rows contain a label outside the valid 17-code vocabulary")

    ok = len(errors) == 0
    return {"ok": ok, "errors": errors, "n_input": len(input_ids), "n_output": len(out_rows)}


# ---------------------------------------------------------------------------
# Step 3: manifest helpers
# ---------------------------------------------------------------------------

def load_manifest(batch_paths):
    if os.path.exists(config.MANIFEST_PATH):
        with open(config.MANIFEST_PATH) as f:
            manifest = json.load(f)
        known = {b["batch_num"]: b for b in manifest["batches"]}
    else:
        manifest = {"batch_size": config.BATCH_SIZE, "total_reviews": 0, "n_batches": 0, "batches": []}
        known = {}

    # Reconcile with freshly-rebuilt batch files (adds any missing entries,
    # keeps existing status e.g. "verified_done" for batches 1-15).
    batches = []
    total = 0
    for batch_num in sorted(batch_paths):
        path = batch_paths[batch_num]
        with open(path, newline="", encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1
        total += n
        entry = known.get(batch_num, {"batch_num": batch_num, "path": path, "n": n, "status": "pending"})
        entry["path"] = path
        entry["n"] = n
        batches.append(entry)

    manifest["batches"] = batches
    manifest["total_reviews"] = total
    manifest["n_batches"] = len(batches)
    return manifest


def save_manifest(manifest):
    with open(config.MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def result_path(batch_num):
    return os.path.join(config.RESULTS_DIR, f"batch_{batch_num:03d}.csv")


# ---------------------------------------------------------------------------
# Step 4: prompt construction (token-lean: integer index, not the full hash)
# ---------------------------------------------------------------------------

PROMPT_HEADER = """You are classifying mobile-app store reviews of retail trading/investing apps into a fixed multi-label taxonomy.

TAXONOMY (17 codes):
{taxonomy}

TASK
For each numbered review below, assign ONE OR MORE of the 17 codes above (multi-label — a review often raises more than one distinct concern). Use GENERAL_SENTIMENT only when none of the 16 substantive codes apply.

OUTPUT FORMAT — STRICT
Output exactly one line per review, in the same order as given, and nothing else (no preamble, no explanation, no markdown, no blank lines):
<number>|<CODE1>|<CODE2>...

Example:
1|USABILITY_NAV
2|APP_STABILITY_PERFORMANCE|CUSTOMER_SUPPORT
3|GENERAL_SENTIMENT

You MUST output exactly {n} lines, numbered 1 to {n}, with no gaps and no duplicates.

REVIEWS ([app]  text):
{reviews}"""


def build_request(batch_num, rows):
    lines = []
    for i, r in enumerate(rows, start=1):
        text = (r["review_text"] or "").replace("\n", " ").strip()
        lines.append(f"{i}. [{r['app']}] {text}")
    prompt = PROMPT_HEADER.format(
        taxonomy=config.TAXONOMY_BLOCK,
        n=len(rows),
        reviews="\n".join(lines),
    )
    return {
        "custom_id": f"batch_{batch_num:03d}",
        "params": {
            "model": config.MODEL_ID,
            "max_tokens": config.MAX_TOKENS,
            # Claude Sonnet 5 has adaptive thinking ON BY DEFAULT (unlike 4.6),
            # and thinking tokens count against max_tokens. Without this, the
            # model was spending its entire token budget on internal reasoning
            # and never writing the actual answer (stop_reason=max_tokens,
            # empty text). This task is pure structured extraction and gets
            # no benefit from reasoning, so thinking is disabled explicitly.
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": prompt}],
        },
    }


def parse_response_text(text, rows):
    """Map the model's '<index>|CODE|CODE' lines back onto review_id_hash."""
    out = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        idx_str, rest = line.split("|", 1)
        idx_str = idx_str.strip()
        if not idx_str.isdigit():
            continue
        idx = int(idx_str)
        if idx < 1 or idx > len(rows):
            continue
        labels = rest.strip()
        out[idx] = labels
    results = []
    for i, r in enumerate(rows, start=1):
        results.append({"review_id_hash": r["review_id_hash"], "labels": out.get(i, "")})
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY in your environment before running this script.")

    batch_paths = build_batches()
    manifest = load_manifest(batch_paths)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)

    # A batch counts as done if its result file exists AND passes verification.
    pending = []
    already_done = []
    for entry in manifest["batches"]:
        batch_num = entry["batch_num"]
        out_path = result_path(batch_num)
        if os.path.exists(out_path):
            v = verify(entry["path"], out_path)
            if v["ok"]:
                entry["status"] = "verified_done"
                already_done.append(batch_num)
                continue
        entry["status"] = "pending"
        pending.append(entry)

    save_manifest(manifest)
    print(f"{len(already_done)} batches already verified-done (skipped): {already_done[:5]}{'...' if len(already_done) > 5 else ''}")
    print(f"{len(pending)} batches pending, will be submitted now.")

    if not pending:
        print("Nothing to submit. Combining results...")
        combine_results(manifest)
        return

    client = Anthropic(api_key=api_key)

    # Build all pending requests
    requests = []
    rows_by_batch = {}
    for entry in pending:
        batch_num = entry["batch_num"]
        with open(entry["path"], newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        rows_by_batch[batch_num] = rows
        requests.append(build_request(batch_num, rows))

    print(f"Submitting {len(requests)} requests as one Message Batches API job...")
    batch_job = client.messages.batches.create(requests=requests)
    print(f"Batch job id: {batch_job.id}  status: {batch_job.processing_status}")

    # Poll until done
    while True:
        status = client.messages.batches.retrieve(batch_job.id)
        counts = status.request_counts
        print(f"  status={status.processing_status}  "
              f"succeeded={counts.succeeded} errored={counts.errored} "
              f"processing={counts.processing} canceled={counts.canceled} expired={counts.expired}")
        if status.processing_status == "ended":
            break
        time.sleep(30)

    # Retrieve + write + verify each result
    newly_done = []
    errored_batches = []
    for result in client.messages.batches.results(batch_job.id):
        custom_id = result.custom_id
        batch_num = int(custom_id.split("_")[1])
        rows = rows_by_batch[batch_num]
        entry = next(e for e in manifest["batches"] if e["batch_num"] == batch_num)

        if result.result.type != "succeeded":
            errored_batches.append((batch_num, result.result.type))
            entry["status"] = f"api_error:{result.result.type}"
            continue

        message = result.result.message
        text = "".join(block.text for block in message.content if block.type == "text")
        parsed = parse_response_text(text, rows)

        out_path = result_path(batch_num)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["review_id_hash", "labels"])
            w.writeheader()
            w.writerows(parsed)

        v = verify(entry["path"], out_path)
        if v["ok"]:
            entry["status"] = "verified_done"
            newly_done.append(batch_num)
        else:
            entry["status"] = "failed_verification"
            print(f"  batch {batch_num:03d} FAILED verification: {v['errors']}")

    save_manifest(manifest)

    print(f"\n{len(newly_done)} newly verified-done.")
    if errored_batches:
        print(f"{len(errored_batches)} batches had an API-level error (re-run this script to retry them): {errored_batches}")
    failed = [e["batch_num"] for e in manifest["batches"] if e["status"] == "failed_verification"]
    if failed:
        print(f"{len(failed)} batches failed verification (re-run this script to retry them): {failed}")

    combine_results(manifest)


def combine_results(manifest):
    done = [e for e in manifest["batches"] if e["status"] == "verified_done"]
    done.sort(key=lambda e: e["batch_num"])
    with open(config.COMBINED_OUTPUT_CSV, "w", newline="", encoding="utf-8") as out_f:
        w = csv.writer(out_f)
        w.writerow(["review_id_hash", "labels"])
        for e in done:
            with open(result_path(e["batch_num"]), newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    w.writerow(row)
    print(f"\nCombined {len(done)}/{len(manifest['batches'])} verified batches "
          f"({sum(e['n'] for e in done)} reviews) into {config.COMBINED_OUTPUT_CSV}")
    if len(done) < len(manifest["batches"]):
        print("Not all batches are done yet — re-run this script to submit/retry the rest.")


if __name__ == "__main__":
    main()
