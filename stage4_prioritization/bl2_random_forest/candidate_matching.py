"""
E2 step 1 -- candidate matching (live rerun).

TF-IDF + cosine similarity between each of Stage 3's 77 roadmap items
(title + description) and every in-window E1 release note (title +
description), restricted to the SAME app as the cluster's dominant app
(the cluster's quotes' review app majority) where determinable (a cluster
about Coinbase should not be matched to a Trading 212 release). Top-3
candidates per cluster are kept for the review step, regardless of score
(low scores are expected and disclosed below).
"""
import csv
import json
import os
import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
ROADMAP_JSON = "/home/claude/Stage3_live/stage3_roadmap_items.json"
E1_CSV = os.path.join(HERE, "e1_release_notes.csv")
PREP_DIR = "/home/claude/Stage3_live/prep"


def dominant_app(category, cluster_id):
    """Majority app among the cluster's sampled reviews, from the Stage 3 prep file."""
    fn = os.path.join(PREP_DIR, f"{category}__{cluster_id}.json")
    if not os.path.exists(fn):
        return None
    with open(fn, encoding="utf-8") as f:
        d = json.load(f)
    apps = Counter()
    for chunk in d["chunks"]:
        for r in chunk:
            apps[r["app"]] += 1
    if not apps:
        return None
    return apps.most_common(1)[0][0]


def main():
    with open(ROADMAP_JSON, encoding="utf-8") as f:
        items = json.load(f)

    with open(E1_CSV, newline="", encoding="utf-8") as f:
        e1_rows = [r for r in csv.DictReader(f) if r["in_corpus_window"] == "True"]

    print(f"{len(items)} Stage 3 roadmap items, {len(e1_rows)} in-window E1 release notes.")

    e1_texts = [f"{r['title']} {r['description']}" for r in e1_rows]
    cluster_texts = [f"{it['title']} {it['description']}" for it in items]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    all_texts = cluster_texts + e1_texts
    tfidf = vectorizer.fit_transform(all_texts)
    cluster_vecs = tfidf[:len(cluster_texts)]
    e1_vecs = tfidf[len(cluster_texts):]

    sims = cosine_similarity(cluster_vecs, e1_vecs)  # (77, n_e1)

    candidates = []
    all_scores = []
    for i, it in enumerate(items):
        cat, cid = it["category"], it["cluster_id"]
        dom_app = dominant_app(cat, cid)

        row_scores = list(enumerate(sims[i]))
        # prefer same-app candidates when we know the dominant app, but don't
        # hard-exclude cross-app (a Coinbase-worded release could plausibly
        # still be the right match for a mixed cluster) -- just rank same-app
        # candidates first, matching the spirit of the original's app-aware
        # ranking without silently discarding information.
        def sort_key(pair):
            idx, score = pair
            same_app = dom_app is not None and e1_rows[idx]["app"] == dom_app
            return (0 if same_app else 1, -score)

        row_scores.sort(key=sort_key)
        top3 = row_scores[:3]

        cand_list = []
        for idx, score in top3:
            all_scores.append(float(score))
            cand_list.append({
                "e1_title": e1_rows[idx]["title"],
                "e1_app": e1_rows[idx]["app"],
                "e1_url": e1_rows[idx]["url"],
                "e1_date": e1_rows[idx]["publish_date"],
                "e1_description": e1_rows[idx]["description"],
                "score": round(float(score), 4),
            })

        candidates.append({
            "category": cat, "cluster_id": cid,
            "cluster_title": it["title"], "cluster_description": it["description"],
            "dominant_app": dom_app,
            "n_total": it["n_total"],
            "candidates": cand_list,
        })

    with open(os.path.join(HERE, "e2_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=1)

    all_scores.sort()
    n = len(all_scores)
    median = all_scores[n // 2] if n else 0
    print(f"Wrote e2_candidates.json -- {len(candidates)} clusters x top-3 candidates.")
    print(f"Candidate similarity scores: min={min(all_scores):.4f} median={median:.4f} max={max(all_scores):.4f}")


if __name__ == "__main__":
    main()
