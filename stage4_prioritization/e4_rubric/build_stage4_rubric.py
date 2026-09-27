"""
Stage 4 rubric -- live rerun. Merges the 5 programmatically-computed
dimensions (reach, severity, engagement, recency, cross_platform -- computed
in the earlier data-prep step and stored on stage4_input_items_live.json)
with the 2 genuinely-judged fields (actionability, overall_priority +
justification, from rubric_judgment_scores.py) into one final scored file,
stage4_scores_merged_live.json -- one row per cluster, 77 total.
"""
import json
from rubric_judgment_scores import JUDGMENT

with open("stage4_input_items_live.json") as f:
    items = json.load(f)

out = []
for it in items:
    key = (it["category"], it["cluster_id"])
    actionability, overall_priority, justification = JUDGMENT[key]
    out.append({
        "category": it["category"], "cluster_id": it["cluster_id"],
        "title": it["title"],
        "reach": it["reach_score"], "severity": it["severity_score"],
        "engagement": it["engagement_score"], "recency": it["recency_score"],
        "cross_platform_generality": it["cross_platform_score"],
        "actionability": actionability,
        "overall_priority": overall_priority,
        "justification": justification,
        "n_reviews": it["n_reviews"], "avg_rating": it["avg_rating"],
    })

with open("stage4_scores_merged_live.json", "w") as f:
    json.dump(out, f, indent=1)

print(f"Wrote {len(out)} scored clusters to stage4_scores_merged_live.json")
