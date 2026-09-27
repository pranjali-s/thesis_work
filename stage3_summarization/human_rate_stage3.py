"""
Stage 3 -- human rating tool (BUILT, NOT RUN).

Disclosure: this tool is built and smoke-tested only. No human has used it
to rate any of the 77 roadmap items in this live run. Everything in
stage3_ratings.json / stage3_ratings_summary.json so far is the AI-only
blind adversarial rating pass (see STAGE3_RUN_LOG.md) -- an explicitly
documented stand-in for, not a substitute for, human validation. This
script is the disclosed upgrade path: a human domain expert (e.g. someone
familiar with these three trading apps and their review base) works
through the same 77 items and records their own faithfulness/clarity/
usefulness judgments, blind to the AI ratings, so the two can later be
compared for agreement (e.g. Cohen's kappa) as an actual validation step
-- something this run has NOT done.

Usage (not executed in this run):
    python3 human_rate_stage3.py
Walks through each of the 77 items in stage3_roadmap_items.json one at a
time in the terminal, shows title/description/quotes (never the AI
rating, to keep the human judgment blind), and prompts for three 1-5
scores plus optional free-text notes. Supports resuming: already-rated
items (by review of an existing output file) are skipped on a re-run.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROADMAP_PATH = os.path.join(HERE, "stage3_roadmap_items.json")
OUT_PATH = os.path.join(HERE, "human_ratings.json")


def load_existing():
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        return {(r["category"], r["cluster_id"]): r for r in existing}
    return {}


def prompt_int(label):
    while True:
        raw = input(f"  {label} (1-5): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 5:
            return int(raw)
        print("    Enter an integer 1-5.")


def main():
    with open(ROADMAP_PATH, encoding="utf-8") as f:
        items = json.load(f)

    done = load_existing()
    results = list(done.values())

    remaining = [it for it in items if (it["category"], it["cluster_id"]) not in done]
    print(f"{len(done)} already rated, {len(remaining)} remaining out of {len(items)} total.")

    for i, it in enumerate(remaining, 1):
        print("\n" + "=" * 90)
        print(f"[{i}/{len(remaining)}] {it['category']} / cluster {it['cluster_id']}  "
              f"(n_total={it['n_total']}, n_sampled={it['n_sampled']})")
        print(f"TITLE: {it['title']}")
        print(f"DESCRIPTION: {it['description']}")
        for q in it.get("quotes", []):
            print(f"  QUOTE ({q['review_id']}): {q['quote']}")

        faithfulness = prompt_int("Faithfulness: does this accurately represent the underlying reviews?")
        clarity = prompt_int("Clarity: is the title/description clear and unambiguous?")
        usefulness = prompt_int("Usefulness: would this be actionable for a product team?")
        notes = input("  Notes (optional): ").strip()

        results.append({
            "category": it["category"], "cluster_id": it["cluster_id"],
            "faithfulness": faithfulness, "clarity": clarity, "usefulness": usefulness,
            "notes": notes, "rater": "human",
        })

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1)

    print(f"\nDone. {len(results)}/{len(items)} items rated. Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
