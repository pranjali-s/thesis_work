"""
Fast terminal tool for YOUR OWN human coding of the 616-review reliability
subsample. This does not classify anything for you — it just removes the
Excel friction (scrolling, clicking cells, hunting for definitions) so your
own judgment can move faster. Every code entered comes from you typing it.

Blinding preserved: the review's source_tag (whether it was a random "base"
row or a purposively-boosted rare-category row) is deliberately NOT shown,
same as the original Excel workbook — you shouldn't know which reviews were
cherry-picked for a category while you're coding them.

Progress is saved to disk after every single review, so you can quit at any
point (Ctrl+C or 'q') and resume later exactly where you left off — nothing
is lost.

Run:
    python3 human_code.py
"""

import csv
import os
import sys
from datetime import datetime, timezone

SUBSAMPLE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "B4_human_reliability_subsample_v2.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "human_coding_results.csv")

CATEGORIES = [
    ("USABILITY_NAV", "Ease/difficulty of using the interface: layout, findability, navigation flow."),
    ("ACCOUNT_ACCESS_AUTH", "Login, password reset, identity verification, 2FA friction, device-change lockouts."),
    ("APP_STABILITY_PERFORMANCE", "Crashes, freezes, lag, slow loading, failure to open/respond."),
    ("FUNDS_TRANSFER", "Linking a bank, moving money in/out, withdrawal limits/holds, delayed funds."),
    ("TRADE_EXECUTION", "Order fulfillment accuracy: execution price, partial fills, order types, restrictions."),
    ("CRYPTO_SPECIFIC", "Crypto transfer failures, staking terms, wallet restrictions, specific-coin coverage."),
    ("TRUST_FAIRNESS_REGULATORY", "Perceived manipulation/self-dealing/unfairness at the business-model level."),
    ("CUSTOMER_SUPPORT", "Access to/quality of human support: wait times, chatbot loops, unresolved tickets."),
    ("CHARTING_TOOLS", "Depth/quality of charts, indicators, historical data, tools for active traders."),
    ("ONBOARDING_BEGINNER", "Suitability for first-time investors: guided experience, explanatory content."),
    ("FEES_SUBSCRIPTION", "Subscription paywalling, transfer/withdrawal fees, hidden costs, non-consensual enrollment."),
    ("ADVERTISING_NOTIFICATIONS", "In-app upsell messaging, marketing notifications, cross-sell prompts, ad density."),
    ("PREDICTION_MARKETS", "Reactions to the prediction-market/event-contract feature, incl. 'gambling' framing."),
    ("SECURITY_PRIVACY", "Account takeover, unauthorized access, personal/biometric data concerns."),
    ("ACCOUNT_LIFECYCLE", "Opening an account, or closing/deactivating one (incl. unwanted continuation)."),
    ("ASSET_COVERAGE", "Requests for more tradable assets/markets, or jurisdictional access complaints."),
    ("GENERAL_SENTIMENT", "Praise/complaint with NO identifiable specific concern. Use only if NONE of 1-16 apply."),
]
CODE_BY_NUM = {i + 1: c[0] for i, c in enumerate(CATEGORIES)}
VALID_CODES = {c[0] for c in CATEGORIES}


def print_legend():
    print("\n" + "=" * 70)
    for i, (code, definition) in enumerate(CATEGORIES, start=1):
        print(f"  {i:2d}  {code:28s} {definition}")
    print("=" * 70)


def load_reviews():
    with open(SUBSAMPLE_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_done():
    done = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done[r["review_id_hash"]] = r
    return done


def append_result(review_id_hash, labels, note):
    is_new = not os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["review_id_hash", "labels", "note", "coded_at"])
        if is_new:
            w.writeheader()
        w.writerow({
            "review_id_hash": review_id_hash,
            "labels": labels,
            "note": note,
            "coded_at": datetime.now(timezone.utc).isoformat(),
        })
        f.flush()


def parse_input(raw):
    """Returns (labels_str, note) or None if input was invalid/empty."""
    raw = raw.strip()
    if not raw:
        return None
    note = ""
    if "//" in raw:
        raw, note = raw.split("//", 1)
        note = note.strip()
    tokens = raw.replace(",", " ").split()
    codes = []
    for t in tokens:
        if t.isdigit() and int(t) in CODE_BY_NUM:
            codes.append(CODE_BY_NUM[int(t)])
        elif t.upper() in VALID_CODES:
            codes.append(t.upper())
        else:
            print(f"  !! unrecognized code '{t}' — try again (type 'h' for the legend)")
            return "RETRY"
    if not codes:
        return "RETRY"
    # de-dupe, keep order
    seen = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return ("|".join(seen), note)


def main():
    reviews = load_reviews()
    done = load_done()
    remaining = [r for r in reviews if r["review_id_hash"] not in done]

    print(f"\n{len(reviews)} total reviews in the reliability subsample. "
          f"{len(done)} already coded. {len(remaining)} remaining.")
    print("Type one or more category NUMBERS separated by spaces (multi-label OK), e.g.:  1 3")
    print("Optional note: add // after your codes, e.g.:  1 3 // ambiguous, could also be 8")
    print("Commands:  h = show legend   s = skip for now   q = save and quit")

    print_legend()

    last_entered = None  # (review_id_hash, index in remaining) for 'back' support

    i = 0
    while i < len(remaining):
        r = remaining[i]
        n_done_now = len(load_done())
        print(f"\n--- Review {n_done_now + 1}/{len(reviews)}  |  app={r['app']}  rating={r['rating']}  date={r['review_date'][:10]} ---")
        # NOTE: source_tag deliberately not shown — keeps you blind to booster vs base rows.
        text = r["review_text"].strip()
        print(text)
        print("-" * 70)

        raw = input("Codes [h/s/q]: ")
        cmd = raw.strip().lower()

        if cmd == "q":
            print(f"\nSaved. {len(load_done())}/{len(reviews)} coded so far. Run this script again anytime to resume.")
            return
        if cmd == "h":
            print_legend()
            continue
        if cmd == "s":
            print("  skipped — will come back to it later in this session.")
            remaining.append(remaining.pop(i))  # move to end, don't advance i
            continue

        parsed = parse_input(raw)
        if parsed is None or parsed == "RETRY":
            continue

        labels, note = parsed
        append_result(r["review_id_hash"], labels, note)
        last_entered = r["review_id_hash"]
        print(f"  -> saved: {labels}" + (f"   note: {note}" if note else ""))
        i += 1

    print(f"\n🎉 All {len(reviews)} reviews coded! Output: {OUTPUT_CSV}")
    print("Send that file back and I'll compute human-vs-AI reliability once the AI side is run on the same 616.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\nInterrupted — progress is saved (every entry writes immediately). "
              f"Run this script again to resume from where you left off.")
        sys.exit(0)
