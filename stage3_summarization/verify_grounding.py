"""
Stage 3 -- independent grounding/hallucination check.

Per the project's standing rule (never trust a subagent's self-report),
this re-verifies every quote in stage3_roadmap_items.json from scratch,
against the FULL original review text corpus (not just the sampled subset
an agent saw) -- checking both that the cited review_id actually belongs
to that cluster in Stage 2's real output, and that the quote is an exact
(whitespace-normalized) contiguous substring of that review's actual text.
"""
import csv
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BATCHES_DIR = "/home/claude/Stage2_live/batches"
ASSIGNMENTS_CSV = "/home/claude/Stage2_live/clusters/cluster_assignments.csv"


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def load_review_text():
    id_to_text = {}
    for fp in sorted(glob.glob(os.path.join(BATCHES_DIR, "batch_*.csv"))):
        with open(fp, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                id_to_text[row["review_id_hash"]] = row["review_text"] or ""
    return id_to_text


def load_cluster_membership():
    membership = {}  # review_id -> set of (category, cluster_id)
    with open(ASSIGNMENTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            membership.setdefault(row["review_id_hash"], set()).add((row["category"], row["cluster_id"]))
    return membership


def main():
    id_to_text = load_review_text()
    membership = load_cluster_membership()

    with open(os.path.join(HERE, "stage3_roadmap_items.json"), encoding="utf-8") as f:
        items = json.load(f)

    total_quotes = 0
    ungrounded = []
    wrong_cluster = []
    unknown_id = []

    for it in items:
        cat, cid = it["category"], it["cluster_id"]
        for q in it.get("quotes", []):
            total_quotes += 1
            rid = q.get("review_id", "")
            quote = q.get("quote", "")

            if rid not in id_to_text:
                unknown_id.append((cat, cid, rid))
                continue

            if (cat, cid) not in membership.get(rid, set()):
                wrong_cluster.append((cat, cid, rid))

            src = norm(id_to_text[rid])
            if norm(quote) not in src:
                ungrounded.append((cat, cid, rid, quote[:80]))

    print(f"Total quotes checked: {total_quotes}")
    print(f"Unknown review_id (not in corpus at all): {len(unknown_id)}")
    for row in unknown_id[:10]:
        print("  ", row)
    print(f"review_id not actually in that (category, cluster): {len(wrong_cluster)}")
    for row in wrong_cluster[:10]:
        print("  ", row)
    print(f"Quote NOT an exact substring of its review's real text: {len(ungrounded)}")
    for row in ungrounded[:10]:
        print("  ", row)

    ok = not unknown_id and not wrong_cluster and not ungrounded
    print("\n" + ("PASSED -- every quote independently verified grounded." if ok
                   else "FAILED -- see discrepancies above."))

    with open(os.path.join(HERE, "grounding_check_report.json"), "w", encoding="utf-8") as f:
        json.dump({
            "total_quotes": total_quotes,
            "unknown_id": unknown_id,
            "wrong_cluster": wrong_cluster,
            "ungrounded": ungrounded,
            "passed": ok,
        }, f, indent=1)


if __name__ == "__main__":
    main()
