"""
Keyword-based baseline classifier for the 616-review reliability subsample.

IMPORTANT METHODOLOGICAL NOTE — read before using this output in the
thesis: this is NOT human coding. It is a fixed keyword/phrase-pattern
rule engine, applied automatically with no reviewer judgment involved. It
uses the same "operationalize each category as a keyword pattern" approach
already used (and already disclosed as a lower-bound, not an independent
coding instrument) in the 4.3 taxonomy pilot's frequency-validation pass —
so there is real precedent for this as ONE kind of instrument, but it is
a categorically different thing from a second rater's judgment, and
cannot support a genuine inter-rater / human-vs-AI reliability claim.
Concretely: keyword matching will over-trigger on incidental word overlap,
under-trigger on paraphrase/implicit meaning, and cannot resolve ambiguity
the way a human reader can. If this output is used in place of step 3-5 in
the pipeline, the 4.4.1 write-up needs to say plainly that "human
reliability subsample" became a "keyword-baseline concordance check"
instead, and interpret any resulting kappa accordingly (as
keyword-baseline vs. LLM agreement, not human vs. LLM agreement).

Multi-label: a review can match multiple categories' patterns. If nothing
matches, it falls back to GENERAL_SENTIMENT (matching the taxonomy's own
rule that GENERAL_SENTIMENT is used when none of the 16 substantive
categories apply).

Run:
    python3 keyword_baseline_classify.py
Output:
    keyword_baseline_labels.csv   (review_id_hash, labels)
"""

import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SUBSAMPLE_CSV = os.path.join(HERE, "B4_human_reliability_subsample_v2.csv")
OUTPUT_CSV = os.path.join(HERE, "keyword_baseline_labels.csv")

# Same 17-code taxonomy as everywhere else in this project. Patterns are
# case-insensitive substrings/phrases, deliberately conservative (drawn
# from the category definitions in Table 4.8) rather than an exhaustive
# list — see the methodological note above for why this is a lower bound,
# not a validated instrument.
PATTERNS = {
    "USABILITY_NAV": [
        "easy to use", "user friendly", "user-friendly", "hard to navigate",
        "confusing", "intuitive", "hard to find", "can't find", "cannot find",
        "navigat", "clunky interface", "layout", "so simple to use",
    ],
    "ACCOUNT_ACCESS_AUTH": [
        "log in", "login", "logged out", "can't log", "cant log", "password",
        "two factor", "2fa", "verification code", "locked out", "authenticat",
        "face id", "fingerprint login",
    ],
    "APP_STABILITY_PERFORMANCE": [
        "crash", "freeze", "freezing", "lag", "slow to load", "won't open",
        "wont open", "stuck loading", "keeps closing", "glitch", "bug",
    ],
    "FUNDS_TRANSFER": [
        "deposit", "withdraw", "link my bank", "bank account", "transfer money",
        "transfer funds", "held my money", "funds are stuck", "pending transfer",
        "money is stuck",
    ],
    "TRADE_EXECUTION": [
        "order didn't fill", "order execution", "slippage", "limit order",
        "market order", "partial fill", "trade didn't go through",
        "execution price", "order got cancelled",
    ],
    "CRYPTO_SPECIFIC": [
        "crypto", "bitcoin", "ethereum", "staking", "wallet", " coin",
        "btc", "eth ", "altcoin",
    ],
    "TRUST_FAIRNESS_REGULATORY": [
        "scam", "manipulat", "rigged", "unfair", "fraud", "rip off", "ripoff",
        "stealing my money", "shady", "untrustworthy",
    ],
    "CUSTOMER_SUPPORT": [
        "customer service", "customer support", "support team", "no response",
        "chatbot", "can't reach support", "waited days", "support ticket",
        "never got a reply",
    ],
    "CHARTING_TOOLS": [
        "chart", "charting", "technical indicator", "candlestick", "indicators",
        "analysis tools",
    ],
    "ONBOARDING_BEGINNER": [
        "beginner", "new to investing", "first time investing", "easy to start",
        "learning curve", "tutorial", "new investor",
    ],
    "FEES_SUBSCRIPTION": [
        " fee", "fees", "subscription", "gold membership", "hidden cost",
        "charged me", "monthly charge", "hidden fee",
    ],
    "ADVERTISING_NOTIFICATIONS": [
        "too many notifications", "spam", " ads ", "advertisement", "upsell",
        "promo", "constant notifications",
    ],
    "PREDICTION_MARKETS": [
        "prediction market", "event contract", "gambling", "betting app",
        "feels like gambling",
    ],
    "SECURITY_PRIVACY": [
        "hacked", "unauthorized access", "data breach", "stole my", "privacy",
        "biometric data", "personal information", "account was compromised",
    ],
    "ACCOUNT_LIFECYCLE": [
        "close my account", "delete my account", "deactivate", "can't close account",
        "cant close account", "account closure", "open an account", "closing my account",
    ],
    "ASSET_COVERAGE": [
        "doesn't support", "not available in my country", "add more stocks",
        "add more coins", "not offered in", "isa", "more assets", "not available in the uk",
    ],
}

VALID_CODES = set(PATTERNS.keys()) | {"GENERAL_SENTIMENT"}


def classify(text):
    t = text.lower()
    matched = [cat for cat, patterns in PATTERNS.items() if any(p in t for p in patterns)]
    if not matched:
        matched = ["GENERAL_SENTIMENT"]
    return "|".join(matched)


def main():
    with open(SUBSAMPLE_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["review_id_hash", "labels"])
        w.writeheader()
        for r in rows:
            labels = classify(r["review_text"] or "")
            w.writerow({"review_id_hash": r["review_id_hash"], "labels": labels})

    print(f"Classified {len(rows)} reviews -> {OUTPUT_CSV}")
    print("\nReminder: this is a KEYWORD BASELINE, not human coding. See the")
    print("docstring at the top of this script before using it in the thesis write-up.")


if __name__ == "__main__":
    main()
