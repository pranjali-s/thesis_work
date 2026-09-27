# Stage 1 (4.4.1 LLM-based classification) — direct-API handoff package

## What this is and why it exists

This replaces the *execution mechanism* for classifying the ~47,900 reviews
still pending in the full-corpus run (batches 16-175). It does **not**
change the methodology: same model (`claude-sonnet-5`), same 17-code
taxonomy, same multi-label pipe-delimited labels, same independent
per-batch verification (exact row-count match, exact ID-set match, every
label in the valid vocabulary, no empty labels) that batches 1-15 were
already held to.

**Revision note (for your methods write-up):** Batches 1-15 (4,500 reviews)
were produced by dispatching one subagent per 300-review batch inside an
agent-orchestration harness. Each of those calls consumed 95,000-132,000
tokens per batch, almost all of it harness overhead (the subagent's own
tool calls and reasoning) rather than the classification task itself, which
only needs on the order of 15,000-20,000 tokens per batch. This package
performs the identical classification task via direct calls to the
Anthropic Messages API — specifically the **Message Batches API**, which
processes requests asynchronously at a 50% price discount — removing the
harness overhead and cutting the effective cost roughly 8-10x, with the
Batches API discount on top of that. Batches 1-15 are unaffected and are
included in this package so they are not redone.

## What's in this folder

```
classify_reviews.py   the script you run
config.py              model ID, taxonomy text, paths (edit paths here)
requirements.txt       one dependency: the anthropic Python SDK
manifest.json          batch tracker; batches 1-15 already marked verified_done
results/               batch_001.csv ... batch_015.csv, already verified — shipped so you skip re-paying for them
README.md              this file
```

Not included: the 52,392-row corpus CSV itself (`combined_reviews.csv`).
That file is the output of the review-collection step from 4.2, which you
ran yourself — point `config.py` at your own local copy of it (see Step 2
below). The script does not re-download or re-scrape anything.

## Step-by-step guide

**1. Get the files onto your machine.** Put this whole folder somewhere on
your computer, e.g. `~/thesis/Stage1_classification/`.

**2. Point it at your corpus.** Open `config.py` and check the
`CORPUS_CSV` line near the bottom. By default it expects
`combined_reviews.csv` sitting next to the script. Either copy your local
combined_reviews.csv (from your 4.2 data collection run) into this same
folder, or edit `CORPUS_CSV` to the full path where it actually lives. The
file needs the columns `review_id_hash, app, platform, review_text` (plus
whatever else it already has — extra columns are ignored).

**3. Install the one dependency:**
```
pip install -r requirements.txt
```
(If you don't already have Python 3.9+ and pip, install those first —
happy to walk through that separately if needed.)

**4. Set your API key.** You need an Anthropic Console API key (not a
claude.ai subscription — this is a separate pay-as-you-go API account at
[console.anthropic.com](https://console.anthropic.com)). If you don't
already have one, create one there under "API Keys", then in your
terminal:
```
export ANTHROPIC_API_KEY=sk-ant-...
```
(On Windows: `set ANTHROPIC_API_KEY=sk-ant-...` in Command Prompt, or
`$env:ANTHROPIC_API_KEY="sk-ant-..."` in PowerShell.)

**5. Run it:**
```
python3 classify_reviews.py
```
What happens:
- It rebuilds all 175 batches locally from your corpus (deterministic —
  same seed as before, so batch numbering matches batches 1-15 exactly).
- It checks `results/` and skips any batch that already has a verified
  result file (batches 1-15, shipped with this package).
- It submits every remaining pending batch (should be 160, batches 16-175)
  as **one** Message Batches API job.
- It prints the job id, then polls every 30 seconds and prints progress
  (`succeeded / errored / processing`) until Anthropic reports the job
  finished. **This can take anywhere from minutes to a few hours** — Anthropic's
  own SLA allows up to 24h, though in practice batch jobs of this size
  typically finish much faster. You can safely `Ctrl+C` and re-run the
  script later; it will resubmit only what's still pending (though note:
  re-running before the first job finishes will start a *second* job for
  the same batches unless you first cancel or wait it out — just let it
  finish once started).
- As results come back, it writes each batch's result CSV, independently
  re-verifies it (same 4 checks as before), and updates `manifest.json`.
- At the end it prints how many batches are verified-done and writes
  `stage1_full_corpus_labels.csv` — the combined, verified output for
  every batch completed so far.

**6. If anything failed verification or errored,** just run
`python3 classify_reviews.py` again. It only resubmits batches that are
not yet `verified_done`, so this is safe to re-run as many times as needed
and won't re-pay for batches that already succeeded.

**7. When it's done,** send me `stage1_full_corpus_labels.csv` (and the
final `manifest.json`, so I can see the verification trail) and I'll pick
up the evaluation and 4.4.1 write-up from there.

### Optional: test on one batch first

If you want to see the cost and behavior on a small scale before
committing to all 160 batches, you can temporarily rename
`manifest.json` out of the way (so the script treats *no* batches as done)
and then, after the first run rebuilds `batches/`, delete all but
`batches/batch_016.csv` before running — or simplest, just let the full
run start and `Ctrl+C` after the first status print; the job is already
submitted for all 160 at that point though, so if you want a true
single-batch dry run, ask me and I'll give you a 5-line variant that
submits just one batch.

## ⚠️ Incident (2026-09-18): first run failed, real money was spent — read this first

The first run of this script (before the fix below) submitted all 160
remaining batches and **spent real money without producing usable output**.
Root cause: **Claude Sonnet 5 has adaptive thinking turned on by default**
(unlike Sonnet 4.6), and thinking tokens count against `max_tokens`. The
original script didn't set a `thinking` parameter, so every request spent
its entire 8,192-token budget on invisible internal reasoning and got cut
off (`stop_reason: max_tokens`) before writing any — or, for most
batches, *any* — of the actual answer. Diagnosis confirmed via
`diagnose_batch.py`, which re-pulled the (free, already-paid-for) batch
results: all 160/160 responses hit `stop_reason: max_tokens`, for a real
cost of **$8.87** against effectively zero usable rows.

**This is now fixed** in `classify_reviews.py`: every request explicitly
sets `"thinking": {"type": "disabled"}`, since this classification task is
pure structured extraction and gets no benefit from reasoning. With
thinking off, the 8,192-token cap should comfortably cover a real answer
(the original ~$5.30 estimate below should now be roughly accurate again).

**Before re-running on all remaining batches, run the cheap sanity check
first:**
```
python3 test_one_batch.py
```
This sends just one batch (300 reviews) as a normal synchronous call —
costs a few cents, gives you an answer in seconds, and tells you plainly
whether the fix worked (`stop_reason` should now be `end_turn`, not
`max_tokens`, and verification should pass). Only once that succeeds should
you run the full `classify_reviews.py` again.

**On your balance:** if you're down to close to $1, that likely isn't
enough to complete all 160 remaining batches (~$5.30 estimated) even with
the fix — you'll probably need to add more credit at
[console.anthropic.com](https://console.anthropic.com) → Billing before
the full run can finish. The single-batch test above is cheap enough to
run regardless.

## Honest token / cost estimate

I estimated this from the actual review-text lengths in your batch files
(average ~102 characters per review) using the standard ~4-characters-per-token
approximation — **not** an exact tokenizer count, so treat it as a
reasonable planning figure, not a guarantee. The script itself will tell
you the real `request_counts` as it runs.

For the **160 pending batches (47,892 reviews, batches 16-175)**:

| | Estimate |
|---|---|
| Input tokens (taxonomy + instructions + review text, ~12,200/batch) | ≈ 1.95M tokens |
| Output tokens (index + labels per review, ~4,200/batch) | ≈ 0.67M tokens |
| **Cost via Message Batches API** (Sonnet 5: $1/MTok in, $5/MTok out — 50% off standard) | **≈ $5.30** |
| Cost via standard (non-batch) API, for comparison | ≈ $10.60 |

For comparison, the subagent-orchestration approach used for batches 1-15
was running at roughly 95,000-132,000 tokens per 300-review batch. Applied
to the same 160 remaining batches that would be on the order of
15-20 million tokens total — call it **$40-55 at standard per-token
pricing** even before accounting for the fact that most of those tokens
were harness overhead, not classification. So the direct-API/Batches route
here is roughly **8-10x cheaper**, on top of being far less likely to hit
any session-level rate or context limits.

**I cannot see your Anthropic Console balance or usage from here** — this
is a completely separate account/product from your claude.ai subscription.
To check how many credits you currently have, log into
[console.anthropic.com](https://console.anthropic.com) and look under
**Settings → Billing** (current balance) and **Usage** (spend so far). If
you don't yet have a positive balance there, you'll need to add credit
before the script's batch submission will succeed — the API will return a
clear billing error if so, it won't fail silently.
