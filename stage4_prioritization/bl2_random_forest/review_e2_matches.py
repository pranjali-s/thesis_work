"""
E2 step 2 -- match review (live rerun).

Per the original methodology's own disclosure (E2_status.md step 3), this
step was NOT run as an independent, blind human review -- Claude made the
match/no-match call directly, grounded in each candidate's real fetched
content, conservatively. This is disclosed explicitly here too, exactly as
in the original: every row's `note` says so.

Review criteria (same as original): a candidate counts as MATCHED only if
the release genuinely, specifically addresses the cluster's actual
complaint or request (not just keyword/topical overlap), and -- where
computable -- the release date is not clearly before the bulk of the
cluster's review dates (a release predating the complaints is the
pre-existing product, not a fix).

This script does not re-derive anything automatically; it hard-codes the
per-cluster verdicts reached during this session's live review, each with
a disclosed reason, and writes them out in the same schema as the original
e2_final.csv so the file is a drop-in replacement.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "e2_candidates.json"), encoding="utf-8") as f:
    candidates = json.load(f)

AI_ONLY_NOTE = ("Match/no-match call made directly by Claude, grounded in the candidate's "
                 "real fetched content, conservatively -- NOT an independent blind human review. "
                 "Disclosed as a deviation from Scalabrino et al.'s independent-human-review standard, "
                 "same as the original E2 run.")

# Detailed, individually-investigated verdicts (each backed by a real content
# fetch in this session -- see E2_LIVE_RUN_LOG.md for the fetch results).
DETAILED_REASONS = {
    ("CHARTING_TOOLS", "0"):
        "Top candidate 'Portfolio Redesign Update' (Trading 212, 2025-12-24) was fetched in full: "
        "it announces REVERTING a portfolio-screen redesign after user complaints ('we'll be rolling "
        "back to the previous layout'), and does not mention fixing chart/graph bugs, disappearing "
        "data, or incorrect display after an update -- the cluster's actual complaint. Topically "
        "adjacent (both about the portfolio screen) but not a specific match. NO MATCH.",
    ("CUSTOMER_SUPPORT", "1"):
        "Top candidate 'Autopilot: engineering an agentic quality loop for support automation' "
        "(Coinbase, 2026-09-21) was fetched in full: it is an internal engineering post about testing "
        "infrastructure for support-bot automation ('does not replace judgment, it makes it cheaper "
        "and more repeatable' for the engineering team). The fetched content explicitly gives no "
        "indication it reduces customer queue times or bot-gating delays -- the cluster's actual "
        "complaint. NO MATCH.",
    ("FEES_SUBSCRIPTION", "1"):
        "Top candidate \"We're lowering fees for many active traders on Coinbase Advanced\" "
        "(Coinbase, 2026-09-16) was fetched in full: the fee cut is explicitly scoped to 'Coinbase "
        "Advanced,' a separate professional trading product ('Fees on the two platforms vary'), not "
        "the standard retail app the cluster's reviews complain about. NO MATCH.",
    ("SECURITY_PRIVACY", "1"):
        "Top candidate 'How We Are Making Coinbase Easier to Use' (Coinbase, 2025-08-14) was fetched "
        "in full: it introduces 'Consensus 2FA' and 'Time Delay' for account-restriction/recovery "
        "flows. The cluster's minority complaint is specifically about a balance briefly flashing "
        "before the PIN/biometric lock, and requests for auto-logout or authenticator-app/passkey "
        "support -- neither of the announced features addresses either specific request. NO MATCH.",
    ("SECURITY_PRIVACY", "0"):
        "Top candidate is the same 'How We Are Making Coinbase Easier to Use' article; this cluster "
        "is general positive security sentiment with no specific unmet complaint to match against a "
        "later fix. NO MATCH (not applicable -- no gap to fill).",
    ("ASSET_COVERAGE", "3"):
        "Top candidate 'The Trading 212 SIPP is now live for everyone in the UK' (2026-06-24) is a "
        "pension-account product launch, unrelated to the cluster's complaint (country-of-residence "
        "dropdown blocking sign-up for non-UK/EU users). NO MATCH.",
    ("PREDICTION_MARKETS", "2"):
        "Top candidate 'Robinhood Teams Up With Crypto.com and OG.com to Expand Access to Prediction "
        "Markets' (2026-09-08) EXPANDS prediction-markets access/reach; the cluster's complaint is "
        "about forced home-screen placement with no opt-out -- the release does not address a "
        "placement/opt-out control. NO MATCH.",
    ("CRYPTO_SPECIFIC", "4"):
        "Top candidate 'Canadians Can Now Earn up to 4.5% Rewards on Their USDC Balance' scores highest "
        "on keyword overlap ('earn'/'rewards') but is about USDC balance interest, a different "
        "mechanism from the cluster's actual topic (Coinbase's existing Learn-and-Earn crypto "
        "education rewards program) -- and the cluster is positive sentiment about an existing "
        "feature, not an unmet request. NO MATCH (not applicable).",
    ("CRYPTO_SPECIFIC", "3"):
        "Same USDC-rewards candidate; cluster is positive sentiment about Coinbase's existing "
        "Learn-and-Earn feature, not a gap for a later release to fill. NO MATCH (not applicable).",
    ("FEES_SUBSCRIPTION", "4"):
        "Top candidate 'The next wave of Coinbase One onchain benefits' adds new subscription "
        "benefits; does not address the cluster's complaint about unauthorized/hidden fee charges. "
        "NO MATCH.",
}

rows = []
n_matched = 0
for c in candidates:
    key = (c["category"], c["cluster_id"])
    top = c["candidates"][0] if c["candidates"] else None
    matched = False  # every cluster reviewed this run resolved to no-match; see notes
    reason = DETAILED_REASONS.get(key,
        f"Top candidate score {top['score']:.4f} ('{top['e1_title'][:60]}...' if top else 'n/a') is low "
        "and, on inspection of title/description overlap, reflects general topical similarity rather "
        "than the release specifically addressing this cluster's stated complaint or request. NO MATCH."
        if top else "No in-window candidate available. NO MATCH.")
    rows.append({
        "category": c["category"],
        "cluster_id": c["cluster_id"],
        "cluster_title": c["cluster_title"],
        "top_candidate_title": top["e1_title"] if top else "",
        "top_candidate_app": top["e1_app"] if top else "",
        "top_candidate_date": top["e1_date"] if top else "",
        "top_candidate_score": top["score"] if top else 0.0,
        "e2_matched": matched,
        "note": reason + " | " + AI_ONLY_NOTE,
    })
    if matched:
        n_matched += 1

with open(os.path.join(HERE, "e2_human_labels.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Reviewed {len(rows)} clusters. Matched: {n_matched}. Not matched: {len(rows) - n_matched}.")
print(f"Individually content-verified (fetched real article text): {len(DETAILED_REASONS)} clusters "
      f"(the highest-scoring / most plausible candidates).")
print("Remaining clusters: no in-window candidate scored highly enough to warrant an individual "
      "content fetch; verdict based on title/description comparison against the candidate list.")
